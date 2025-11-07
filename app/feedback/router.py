from __future__ import annotations

import json
import os
from calendar import monthrange
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from ..db import get_session
from ..config_feedback import get_feedback_settings
from ..models import User
from .costs import estimate_cost_eur
from .models import FeedbackCache, FeedbackEvent
from .schemas import FeedbackGenerateIn, FeedbackGenerateOut, FeedbackSummaryIn, FeedbackSummaryOut
from .clients import (
    call_anthropic,
    call_local_llama,
    call_openai_gpt,
    count_tokens_estimate,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])
FEEDBACK_SETTINGS = get_feedback_settings()
FEEDBACK_MONTHLY_CAP_EUR = float(os.getenv("FEEDBACK_MONTHLY_CAP_EUR", "50.0"))
FEEDBACK_CAP_MODE = os.getenv("FEEDBACK_CAP_MODE", "mini-only")


def _scalar(value):
    if isinstance(value, tuple):
        return value[0]
    return value


def _month_bounds_utc(dt: datetime) -> tuple[datetime, datetime]:
    start = datetime(dt.year, dt.month, 1)
    last_day = monthrange(dt.year, dt.month)[1]
    end = datetime(dt.year, dt.month, last_day, 23, 59, 59, 999999)
    return start, end


def get_monthly_spend(session: Session) -> float:
    now = datetime.utcnow()
    start, end = _month_bounds_utc(now)
    total = session.exec(
        select(func.sum(FeedbackEvent.cost_eur)).where(
            FeedbackEvent.created_at >= start,
            FeedbackEvent.created_at <= end,
        )
    ).one()
    return float(total or 0.0)


def choose_model(summary_json: dict, difficulty: int | None, language: str) -> str:
    size = len(json.dumps(summary_json))
    if size <= 1500 and (difficulty is None or difficulty <= 3):
        return "mini:haiku4_5"
    if size <= 6000:
        return "pro:sonnet3_7"
    return "local:llama70b"


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def make_cache_key(
    user_id: str,
    persona: str,
    topic: str | None,
    lang: str,
    summary_json: dict,
    max_sentences: int,
) -> str:
    blob = f"{user_id}|{persona}|{topic}|{lang}|{max_sentences}|{json.dumps(summary_json, sort_keys=True)}"
    return sha256(blob.encode("utf-8")).hexdigest()


def pro_check(user: User | None) -> None:
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    is_pro = getattr(user, "is_pro", None)
    pro_until = getattr(user, "pro_until", None)
    if is_pro is True:
        return
    if pro_until and pro_until > datetime.utcnow():
        return
    raise HTTPException(status_code=402, detail="Pro plan required")


def parse_user_id(raw: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user_id") from exc


async def call_llm(model: str, prompt: str, language: str) -> str:
    if model == "mini:gpt4_1":
        text, _ = await call_openai_gpt(FEEDBACK_SETTINGS.openai_model_mini, prompt)
        return text
    if model == "pro:gpt4_1":
        text, _ = await call_openai_gpt(FEEDBACK_SETTINGS.openai_model_pro, prompt)
        return text
    if model == "mini:haiku4_5":
        text, _ = await call_anthropic(FEEDBACK_SETTINGS.anthropic_model_mini, prompt)
        return text
    if model == "pro:sonnet3_7":
        text, _ = await call_anthropic(FEEDBACK_SETTINGS.anthropic_model_pro, prompt)
        return text
    if model == "local:llama70b":
        text, _ = await call_local_llama("llama-3.1-70b-instruct", prompt)
        return text
    return "Here's personalized feedback: keep a steady study cadence and review recent mistakes in small batches."


def build_prompt(persona: str, language: str, max_sentences: int, summary_json: dict, topic: str | None) -> str:
    if language == "fi":
        return (
            f"Olet Teski, persoonana {persona}. Tiivistä opiskelijan viikon oppiminen "
            f"{max_sentences} lauseeseen. Keskity vahvuuksiin, virheisiin ja seuraaviin askeleisiin. "
            f"Aihe: {topic or '-'}\nYhteenveto:\n{json.dumps(summary_json, ensure_ascii=False)}"
        )
    return (
        f"You are Teski, persona={persona}. Summarize the student's week in {max_sentences} sentences. "
        f"Focus on strengths, mistakes, and next steps. Topic: {topic or '-'}\nSummary:\n{json.dumps(summary_json)}"
    )


@router.post("/generate", response_model=FeedbackGenerateOut)
async def generate_feedback(payload: FeedbackGenerateIn, session: Session = Depends(get_session)):
    user_uuid = parse_user_id(payload.user_id)
    user = session.get(User, user_uuid)
    pro_check(user)

    cache_key = make_cache_key(
        payload.user_id,
        payload.persona,
        payload.topic,
        payload.language,
        payload.summary_json,
        payload.max_sentences,
    )
    cached = session.exec(select(FeedbackCache).where(FeedbackCache.key_hash == cache_key)).first()
    if cached:
        session.add(
            FeedbackEvent(
                user_id=payload.user_id,
                model_used=cached.model_used,
                tokens_in=cached.tokens_in,
                tokens_out=cached.tokens_out,
                cost_eur=0.0,
                cached_hit=True,
            )
        )
        session.commit()
        return FeedbackGenerateOut(
            feedback=cached.feedback_text,
            model_used=cached.model_used,
            cached=True,
            estimated_tokens_in=cached.tokens_in,
            estimated_tokens_out=cached.tokens_out,
            estimated_cost_eur=0.0,
        )

    month_spend = get_monthly_spend(session)
    forced_mini: str | None = None
    if month_spend >= FEEDBACK_MONTHLY_CAP_EUR:
        if FEEDBACK_CAP_MODE == "block":
            raise HTTPException(status_code=429, detail="Feedback temporarily unavailable: monthly cap reached")
        forced_mini = "mini:haiku4_5"

    model = forced_mini if forced_mini else choose_model(payload.summary_json, payload.difficulty, payload.language)
    prompt = build_prompt(payload.persona, payload.language, payload.max_sentences, payload.summary_json, payload.topic)
    est_in = estimate_tokens(prompt)
    est_out = 220
    feedback_text = await call_llm(model, prompt, payload.language)
    real_out = count_tokens_estimate(feedback_text, "gpt-4o-mini")
    est_out = real_out or est_out
    est_cost = estimate_cost_eur(model, est_in, est_out)

    cache_row = FeedbackCache(
        key_hash=cache_key,
        model_used=model,
        language=payload.language,
        persona=payload.persona,
        topic=payload.topic,
        feedback_text=feedback_text,
        tokens_in=est_in,
        tokens_out=est_out,
        cost_eur=est_cost,
    )
    session.add(cache_row)
    session.add(
        FeedbackEvent(
            user_id=payload.user_id,
            model_used=model,
            tokens_in=est_in,
            tokens_out=est_out,
            cost_eur=est_cost,
            cached_hit=False,
        )
    )
    session.commit()

    return FeedbackGenerateOut(
        feedback=feedback_text,
        model_used=model,
        cached=False,
        estimated_tokens_in=est_in,
        estimated_tokens_out=est_out,
        estimated_cost_eur=est_cost,
    )


@router.post("/summary", response_model=FeedbackSummaryOut)
async def make_summary(payload: FeedbackSummaryIn, session: Session = Depends(get_session)):
    summary = {
        "window_days": payload.window_days,
        "counts": {"reviews": 42, "correct": 31, "incorrect": 11},
        "mistakes": {"near_miss": 3, "sign": 2, "unit": 1, "concept": 5},
        "streak_days": 4,
        "focus_topics": ["kinematics", "limits"],
    }
    return FeedbackSummaryOut(summary_json=summary)


@router.get("/admin/stats/cache")
async def feedback_cache_stats(session: Session = Depends(get_session)):
    total = _scalar(session.exec(select(func.count(FeedbackCache.id))).one()) or 0
    month_ago = datetime.utcnow() - timedelta(days=30)
    last30 = (
        _scalar(
            session.exec(
                select(func.count(FeedbackCache.id)).where(FeedbackCache.created_at >= month_ago)
            ).one()
        )
        or 0
    )
    return {"total_cached": int(total), "cached_last_30d": int(last30)}


@router.get("/admin/stats/costs")
async def feedback_cost_stats(session: Session = Depends(get_session)):
    month_ago = datetime.utcnow() - timedelta(days=30)
    total_cost = _scalar(session.exec(select(func.sum(FeedbackEvent.cost_eur))).one()) or 0.0
    cost_30d = (
        _scalar(
            session.exec(
                select(func.sum(FeedbackEvent.cost_eur)).where(FeedbackEvent.created_at >= month_ago)
            ).one()
        )
        or 0.0
    )
    total_events = _scalar(session.exec(select(func.count(FeedbackEvent.id))).one()) or 0
    total_hits = (
        _scalar(
            session.exec(
                select(func.count(FeedbackEvent.id)).where(FeedbackEvent.cached_hit.is_(True))
            ).one()
        )
        or 0
    )
    hit_rate = float(total_hits) / float(total_events) if total_events else 0.0
    return {
        "cost_total_eur": float(total_cost),
        "cost_last_30d_eur": float(cost_30d),
        "events_total": int(total_events),
        "cache_hit_rate": hit_rate,
    }


@router.delete("/admin/cache/purge")
async def feedback_cache_purge(session: Session = Depends(get_session)):
    cutoff = datetime.utcnow() - timedelta(days=90)
    rows = session.exec(select(FeedbackCache).where(FeedbackCache.created_at < cutoff)).all()
    purged = 0
    for row in rows:
        session.delete(row)
        purged += 1
    session.commit()
    return {"purged": purged, "older_than_days": 90}
