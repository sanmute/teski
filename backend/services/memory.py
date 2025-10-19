# >>> MEMORY START
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from backend.models_memory import MemoryStat, MistakeLog, ResurfacePlan
from backend.settings import memory_settings


DECAY_HALF_LIFE_DAYS = memory_settings.DECAY_HALF_LIFE_DAYS


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _priority(m: MistakeLog) -> float:
    occurred_at = m.occurred_at or _now_utc()
    age_seconds = max(0.0, (_now_utc() - occurred_at).total_seconds())
    age_days = age_seconds / 86400.0
    decay = 0.5 ** (age_days / DECAY_HALF_LIFE_DAYS)
    resolved_factor = 1.25 if m.resolved_at is None else 0.65
    return m.weight * decay * resolved_factor


def log_mistake(
    session: Session,
    *,
    user_id: int,
    skill_id: Optional[int],
    template_code: Optional[str],
    instance_id: Optional[int],
    error_type: str,
    detail: Dict[str, Any],
) -> MistakeLog:
    now = _now_utc()
    mistake = MistakeLog(
        user_id=user_id,
        skill_id=skill_id,
        template_code=template_code,
        instance_id=instance_id,
        error_type=error_type,
        detail=detail,
        occurred_at=now,
    )
    session.add(mistake)

    stat_stmt = select(MemoryStat).where(MemoryStat.user_id == user_id, MemoryStat.skill_id == skill_id)
    stat = session.exec(stat_stmt).first()
    if stat is None:
        stat = MemoryStat(
            user_id=user_id,
            skill_id=skill_id,
            mistake_count=1,
            last_missed_at=now,
            stability=0.3,
        )
        session.add(stat)
    else:
        stat.mistake_count += 1
        stat.last_missed_at = now
        stat.stability = max(0.2, stat.stability * 0.9)

    session.commit()
    session.refresh(mistake)
    return mistake


def mark_mastered(
    session: Session, *, user_id: int, skill_id: Optional[int], template_code: Optional[str]
) -> None:
    now = _now_utc()
    recent_stmt = (
        select(MistakeLog)
        .where(
            MistakeLog.user_id == user_id,
            MistakeLog.template_code == template_code,
            MistakeLog.resolved_at.is_(None),
        )
        .order_by(MistakeLog.occurred_at.desc())
    )
    recent = session.exec(recent_stmt).all()
    for entry in recent[:3]:
        entry.resolved_at = now
        entry.weight = max(0.1, entry.weight * 0.5)

    stat_stmt = select(MemoryStat).where(MemoryStat.user_id == user_id, MemoryStat.skill_id == skill_id)
    stat = session.exec(stat_stmt).first()
    if stat is None:
        stat = MemoryStat(
            user_id=user_id,
            skill_id=skill_id,
            mistake_count=0,
            last_mastered_at=now,
            stability=0.4,
        )
        session.add(stat)
    else:
        stat.last_mastered_at = now
        stat.stability = min(3.0, stat.stability * 1.15)

    session.commit()


def build_resurface_plan(
    session: Session, *, user_id: int, count: int = 3, horizon_minutes: int = 1440
) -> List[ResurfacePlan]:
    stmt = select(MistakeLog).where(MistakeLog.user_id == user_id, MistakeLog.resolved_at.is_(None))
    mistakes = session.exec(stmt).all()
    if not mistakes:
        return []

    ranked = sorted(mistakes, key=_priority, reverse=True)
    horizon = _now_utc() + timedelta(minutes=horizon_minutes)
    scheduled: List[ResurfacePlan] = []

    for mistake in ranked[:count]:
        when = _now_utc() + timedelta(minutes=random.choice([10, 20, 30, 45, 60, 90, 120]))
        if when > horizon:
            when = horizon
        plan = ResurfacePlan(
            user_id=user_id,
            skill_id=mistake.skill_id,
            template_code=mistake.template_code,
            scheduled_for=when,
            status="pending",
        )
        session.add(plan)
        scheduled.append(plan)

    session.commit()
    return scheduled


def fetch_next_resurfaced_instances(
    session: Session, *, user_id: int, count: int = 3
) -> List[Dict[str, Any]]:
    try:
        from backend.services.dfe_tasks import instantiate_for_user  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("instantiate_for_user unavailable; integrate with tasks module.") from exc

    now = _now_utc()
    plans_stmt = (
        select(ResurfacePlan)
        .where(
            ResurfacePlan.user_id == user_id,
            ResurfacePlan.status == "pending",
            ResurfacePlan.scheduled_for <= now,
        )
        .order_by(ResurfacePlan.scheduled_for.asc())
        .limit(count)
    )
    plans = session.exec(plans_stmt).all()

    payload: List[Dict[str, Any]] = []
    for plan in plans:
        template_code = plan.template_code
        if not template_code:
            plan.status = "skipped"
            continue
        try:
            instance, _template = instantiate_for_user(session, template_code, user_id, force_new=True)
            payload.append({"type": "resurface", "template_code": template_code, "instance_id": instance.id})
            plan.status = "served"
        except Exception:
            plan.status = "skipped"

    session.commit()
    return payload
# <<< MEMORY END
