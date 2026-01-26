# >>> MEMORY V1 START
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlmodel import Session, select

from models_memory import MemoryStat, MistakeLog, ReviewCard
from settings import memory_v1_settings
from utils.analytics import emit


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# >>> MEMCAP START
def _is_disabled() -> bool:
    return memory_v1_settings.DISABLE_MEMORY_V1


def _count_pending_cards(session: Session, user_id: int) -> int:
    stmt = select(func.count()).where(
        ReviewCard.user_id == user_id,
        ReviewCard.status.in_(("scheduled", "due")),
    )
    value = session.exec(stmt).one()
    if isinstance(value, tuple):
        value = value[0]
    return int(value or 0)
# <<< MEMCAP END


def classify_error_subtype(detail: Dict[str, Any], fallback: Optional[str] = "recall") -> str:
    reason = (detail.get("reason", "") or "").lower()
    if "unit" in reason:
        return "unit"
    if "sign" in reason or "minus" in reason:
        return "sign"
    if "spell" in reason:
        return "spelling"
    if "near" in reason or "close" in reason:
        return "near_miss"
    if "friend" in reason:
        return "false_friend"
    if "algebra" in reason:
        return "algebra"
    if "concept" in reason:
        return "concept"
    if "format" in reason:
        return "format"
    return fallback or "other"


def sm2_update(easiness: float, interval_days: float, grade_correct: bool) -> Tuple[float, float]:
    quality = 5 if grade_correct else 2
    new_e = max(1.3, easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if interval_days <= 0:
        next_interval = 1.0 if grade_correct else 0.5
    elif interval_days < 6:
        next_interval = 6.0 if grade_correct else max(1.0, interval_days * 0.5)
    else:
        next_interval = interval_days * new_e if grade_correct else max(1.0, interval_days * 0.5)
    return new_e, next_interval


def log_mistake_v1(
    session: Session,
    *,
    user_id: int,
    skill_id: Optional[int],
    template_code: Optional[str],
    instance_id: Optional[int],
    error_type: Optional[str],
    error_subtype: Optional[str],
    detail: Dict[str, Any],
) -> MistakeLog:
    subtype = error_subtype or classify_error_subtype(detail)
    mistake = MistakeLog(
        user_id=user_id,
        skill_id=skill_id,
        template_code=template_code,
        instance_id=instance_id,
        error_type=error_type or "other",
        error_subtype=subtype,
        detail=detail,
        occurred_at=_now(),
    )
    session.add(mistake)

    if template_code:
        rc_stmt = select(ReviewCard).where(
            ReviewCard.user_id == user_id, ReviewCard.template_code == template_code
        )
        card = session.exec(rc_stmt).first()
        if card is None:
            card = ReviewCard(
                user_id=user_id,
                skill_id=skill_id,
                template_code=template_code,
                easiness=2.3,
                stability=0.3,
                last_interval_days=0.0,
                next_review_at=_now() + timedelta(minutes=20),
                status="scheduled",
            )
            session.add(card)
        else:
            card.next_review_at = min(card.next_review_at, _now() + timedelta(minutes=20))
            card.status = "scheduled"
            card.updated_at = _now()

    stat_stmt = select(MemoryStat).where(
        MemoryStat.user_id == user_id,
        MemoryStat.skill_id == skill_id,
    )
    stat = session.exec(stat_stmt).first()
    if stat is None:
        stat = MemoryStat(
            user_id=user_id,
            skill_id=skill_id,
            mistake_count=1,
            last_missed_at=_now(),
            stability=0.3,
        )
        session.add(stat)
    else:
        stat.mistake_count += 1
        stat.last_missed_at = _now()
        stat.stability = max(0.2, stat.stability * 0.9)

    session.commit()
    session.refresh(mistake)
    return mistake


def mark_review_result(
    session: Session, *, user_id: int, template_code: str, correct: bool
) -> Optional[ReviewCard]:
    stmt = select(ReviewCard).where(
        ReviewCard.user_id == user_id,
        ReviewCard.template_code == template_code,
    )
    card = session.exec(stmt).first()
    if card is None:
        return None

    card.easiness, next_interval = sm2_update(card.easiness, card.last_interval_days, correct)
    card.last_interval_days = next_interval
    card.next_review_at = _now() + timedelta(days=next_interval)
    card.status = "completed" if correct else "scheduled"
    previous_result = card.last_result
    card.last_result = bool(correct)
    card.updated_at = _now()

    # >>> BADGE START
    if correct and previous_result is False:
        try:
            stmt = (
                select(MistakeLog)
                .where(
                    MistakeLog.user_id == user_id,
                    MistakeLog.template_code == template_code,
                )
                .order_by(MistakeLog.occurred_at.desc())
                .limit(3)
            )
            recent = list(session.exec(stmt).all())
            recent_fails = [
                m for m in recent if m and (m.error_type in ("mistake", "other"))
            ]
            if len(recent_fails) >= 2:
                emit("badge.nemesis", user_id, {"template_code": template_code})
        except Exception:
            pass
    # <<< BADGE END

    session.commit()
    session.refresh(card)
    return card


def build_reviews(
    session: Session, *, user_id: int, max_new: int = 3, horizon_minutes: int = 1440
) -> int:
    # >>> MEMCAP START
    if _is_disabled():
        return 0
    if _count_pending_cards(session, user_id) > memory_v1_settings.QUEUE_BACKOFF_THRESHOLD:
        return 0
    # <<< MEMCAP END
    now = _now()
    due_cards = session.exec(
        select(ReviewCard).where(
            ReviewCard.user_id == user_id,
            ReviewCard.next_review_at <= now,
        )
    ).all()
    if due_cards:
        return 0

    candidates = session.exec(select(ReviewCard).where(ReviewCard.user_id == user_id)).all()
    if not candidates:
        return 0

    candidates.sort(key=lambda card: card.next_review_at)
    horizon = now + timedelta(minutes=horizon_minutes)
    updated = 0
    for card in candidates[:max_new]:
        card.next_review_at = min(card.next_review_at, horizon)
        card.status = "scheduled"
        card.updated_at = now
        updated += 1

    session.commit()
    return updated


def _instantiate_for_user(
    session: Session, template_code: str, user_id: int, force_new: bool = True
):
    try:
        from services.dfe_tasks import instantiate_for_user  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("instantiate_for_user unavailable; integrate with tasks module.") from exc

    result = instantiate_for_user(session, template_code, user_id, force_new=force_new)
    if isinstance(result, tuple):
        instance = result[0]
    else:
        instance = result
    return instance


def fetch_due_reviews(
    session: Session, *, user_id: int, count: int = 2
) -> List[Dict[str, Any]]:
    # >>> MEMCAP START
    if _is_disabled():
        return []

    served_stmt = select(func.count()).where(
        ReviewCard.user_id == user_id,
        ReviewCard.status == "served",
        ReviewCard.updated_at >= (_now() - timedelta(days=1)),
    )
    served_value = session.exec(served_stmt).one()
    if isinstance(served_value, tuple):
        served_value = served_value[0]
    served_today = int(served_value or 0)
    if served_today >= memory_v1_settings.DAILY_REVIEW_CAP:
        return []
    remaining = max(0, memory_v1_settings.DAILY_REVIEW_CAP - served_today)
    take = min(count, remaining)
    if take <= 0:
        return []
    # <<< MEMCAP END
    now = _now()
    stmt = (
        select(ReviewCard)
        .where(
            ReviewCard.user_id == user_id,
            ReviewCard.next_review_at <= now,
        )
        .order_by(ReviewCard.next_review_at.asc())
    )
    cards = session.exec(stmt).all()

    items: List[Dict[str, Any]] = []
    for card in cards[:take]:
        if not card.template_code:
            card.status = "skipped"
            card.updated_at = now
            continue
        try:
            instance = _instantiate_for_user(session, card.template_code, user_id, force_new=True)
            items.append(
                {
                    "type": "review",
                    "review_card_id": card.id,
                    "template_code": card.template_code,
                    "instance_id": getattr(instance, "id", None),
                }
            )
            card.status = "served"
            card.updated_at = now
        except Exception:
            card.status = "skipped"
            card.updated_at = now
    session.commit()
    return items
# <<< MEMORY V1 END
