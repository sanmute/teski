from __future__ import annotations

import json
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from ..db import get_session
from ..feedback.router import call_llm
from ..prefs.models import UserPrefs
from .models import ConceptMap, ConfidenceLog, ReviewSettings, SelfExplanation
from .schemas import (
    ConceptMapOut,
    ConceptMapSaveIn,
    ConfidenceIn,
    ElaborateIn,
    ElaborateOut,
    ExplainIn,
    ExplainOut,
    HistoryOut,
    SettingsIn,
    SettingsOut,
)
from .stt import transcribe_audio

router = APIRouter(prefix="/deep", tags=["deep-learning"])

EVAL_PROMPT = """You are Teski, evaluating a student's self-explanation.
Topic: {topic}
Explanation: {text}

Score depth 0-100 and return strict JSON:
{{
 "accuracy": 0-5,
 "causal_reasoning": 0-5,
 "examples_or_analogies": 0-5,
 "boundary_conditions": 0-5,
 "misconceptions": ["short strings"],
 "next_prompts": ["short probing questions"]
}}
ONLY return JSON.
"""

ELABORATE_PROMPT = """Student answer on {topic}:
{ans}

Generate ONE probing \"why\" question that exposes reasoning, and then a 2-3 sentence ideal answer.
Return as:
Q: ...
A: ...
"""


def _has_pref(session: Session, user_id: Optional[UUID], field: str) -> bool:
    if not user_id:
        return False
    row = session.exec(select(UserPrefs).where(UserPrefs.user_id == user_id)).first()
    return bool(getattr(row, field, False)) if row else False


def _require_pref(session: Session, user_id: UUID, field: str, message: str) -> None:
    if not _has_pref(session, user_id, field):
        raise HTTPException(status_code=403, detail=message)


@router.post("/explain/submit", response_model=ExplainOut)
async def submit_explanation(payload: ExplainIn, session: Session = Depends(get_session)):
    _require_pref(session, payload.user_id, "allow_llm_feedback", "LLM feedback is disabled in your preferences.")
    _require_pref(
        session,
        payload.user_id,
        "store_self_explanations",
        "Storing self-explanations is disabled in your preferences.",
    )
    prompt = EVAL_PROMPT.format(topic=payload.topic_id, text=payload.text)
    raw = await call_llm("mini:haiku4_5", prompt, "en")
    try:
        rubric: Dict[str, object] = json.loads(raw)
    except Exception:
        rubric = {
            "accuracy": 2,
            "causal_reasoning": 2,
            "examples_or_analogies": 2,
            "boundary_conditions": 1,
            "misconceptions": [],
            "next_prompts": [
                "Give a concrete example.",
                "When would this reasoning fail?",
            ],
        }
    components = [
        float(rubric.get("accuracy", 0)),
        float(rubric.get("causal_reasoning", 0)),
        float(rubric.get("examples_or_analogies", 0)),
        float(rubric.get("boundary_conditions", 0)),
    ]
    score = int(max(0, min(100, 5 * sum(components))))
    row = SelfExplanation(
        user_id=payload.user_id,
        topic_id=payload.topic_id,
        mode=payload.mode,
        transcript=payload.text,
        rubric=rubric,
        score_deep=score,
        next_prompts={"prompts": rubric.get("next_prompts", [])},
    )
    session.add(row)
    session.commit()
    return ExplainOut(score_deep=score, rubric=rubric, next_prompts=row.next_prompts)


@router.post("/explain/transcribe")
async def transcribe_explanation_audio(
    user_id: UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    _require_pref(session, user_id, "allow_voice_stt", "Voice transcription is disabled in your preferences.")
    text = await transcribe_audio(file)
    if not text:
        raise HTTPException(status_code=400, detail="Transcription unavailable")
    return {"text": text}


@router.post("/elaborate", response_model=ElaborateOut)
async def elaborate(payload: ElaborateIn, user_id: Optional[UUID] = None, session: Session = Depends(get_session)):
    if user_id:
        _require_pref(session, user_id, "allow_elaboration_prompts", "Elaboration prompts are disabled in your preferences.")
    txt = await call_llm(
        "mini:haiku4_5",
        ELABORATE_PROMPT.format(topic=payload.topic, ans=payload.user_answer),
        payload.language,
    )
    question, answer = "", ""
    for line in txt.splitlines():
        if line.startswith("Q:"):
            question = line[2:].strip()
        if line.startswith("A:"):
            answer = line[2:].strip()
    if not question:
        question = "Why is this true?"
    if not answer:
        answer = "Because it follows directly from the definition and constraints."
    return ElaborateOut(question=question, model_answer=answer)


@router.post("/confidence/log")
async def log_confidence(payload: ConfidenceIn, session: Session = Depends(get_session)):
    _require_pref(session, payload.user_id, "allow_transfer_checks", "Confidence logging is disabled in your preferences.")
    row = ConfidenceLog(**payload.model_dump())
    session.add(row)
    session.commit()
    return {"status": "ok", "id": row.id}


@router.get("/confidence/calibration")
async def calibration(user_id: UUID, topic_id: str, session: Session = Depends(get_session)):
    _require_pref(session, user_id, "allow_transfer_checks", "Confidence analytics are disabled in your preferences.")
    rows = session.exec(
        select(ConfidenceLog).where(
            ConfidenceLog.user_id == user_id,
            ConfidenceLog.topic_id == topic_id,
        )
    ).all()
    if not rows:
        return {"avg_confidence": 0.0, "accuracy_pct": 0.0, "calibration_error": 0.0}
    avg_conf = sum(r.confidence for r in rows) / len(rows)
    accuracy = 100.0 * (sum(1 for r in rows if r.correct) / len(rows))
    expected = avg_conf * 20.0
    return {
        "avg_confidence": round(avg_conf, 2),
        "accuracy_pct": round(accuracy, 2),
        "calibration_error": round(expected - accuracy, 2),
    }


@router.post("/conceptmap/save", response_model=ConceptMapOut)
async def conceptmap_save(payload: ConceptMapSaveIn, session: Session = Depends(get_session)):
    _require_pref(session, payload.user_id, "allow_concept_maps", "Concept maps are disabled in your preferences.")
    _require_pref(session, payload.user_id, "store_concept_maps", "Saving concept maps is disabled in your preferences.")
    row = session.exec(
        select(ConceptMap).where(
            ConceptMap.user_id == payload.user_id,
            ConceptMap.topic_id == payload.topic_id,
        )
    ).first()
    if row is None:
        row = ConceptMap(
            user_id=payload.user_id,
            topic_id=payload.topic_id,
            graph_json=payload.graph_json,
        )
    else:
        row.graph_json = payload.graph_json
    session.add(row)
    session.commit()
    return ConceptMapOut(topic_id=row.topic_id, graph_json=row.graph_json)


@router.get("/conceptmap/me", response_model=ConceptMapOut)
async def conceptmap_me(user_id: UUID, topic_id: str, session: Session = Depends(get_session)):
    if not _has_pref(session, user_id, "allow_concept_maps") or not _has_pref(session, user_id, "store_concept_maps"):
        return ConceptMapOut(topic_id=topic_id, graph_json={"nodes": [], "edges": []})
    row = session.exec(
        select(ConceptMap).where(
            ConceptMap.user_id == user_id,
            ConceptMap.topic_id == topic_id,
        )
    ).first()
    if not row:
        return ConceptMapOut(topic_id=topic_id, graph_json={"nodes": [], "edges": []})
    return ConceptMapOut(topic_id=row.topic_id, graph_json=row.graph_json)


@router.post("/settings/interleaving", response_model=SettingsOut)
async def set_interleaving(payload: SettingsIn, session: Session = Depends(get_session)):
    row = session.exec(
        select(ReviewSettings).where(ReviewSettings.user_id == payload.user_id)
    ).first()
    if row is None:
        row = ReviewSettings(user_id=payload.user_id, interleaving=payload.interleaving)
    else:
        row.interleaving = payload.interleaving
    session.add(row)
    session.commit()
    return SettingsOut(interleaving=row.interleaving)


@router.get("/explain/history", response_model=HistoryOut)
async def explain_history(user_id: UUID, topic_id: str, session: Session = Depends(get_session)):
    if not (
        _has_pref(session, user_id, "allow_llm_feedback")
        and _has_pref(session, user_id, "store_self_explanations")
    ):
        return HistoryOut(items=[])
    rows = session.exec(
        select(SelfExplanation)
        .where(
            SelfExplanation.user_id == user_id,
            SelfExplanation.topic_id == topic_id,
        )
        .order_by(SelfExplanation.created_at.desc())
        .limit(10)
    ).all()
    items: List[Dict[str, object]] = [
        {"score_deep": r.score_deep, "rubric": r.rubric, "next_prompts": r.next_prompts}
        for r in rows
    ]
    return HistoryOut(items=items)
