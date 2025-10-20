from __future__ import annotations

import hashlib
from typing import Any, Iterable, List
from uuid import UUID

from sqlmodel import Session, select

from app.config import get_settings
from app.models import ABTestAssignment


def _normalize_buckets(buckets: Iterable[str]) -> List[str]:
    normalized = [b.strip() for b in buckets if b.strip()]
    return normalized or ["control"]


def assign(user: Any, experiment: str, buckets: Iterable[str] | None = None) -> str:
    user_id = getattr(user, "id", None) or str(user)
    if not user_id:
        raise ValueError("user identifier required for A/B assignment")

    buckets = _normalize_buckets(buckets or get_settings().AB_BUCKETS)
    key = f"{experiment}:{user_id}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    slot = int(digest[:8], 16) % len(buckets)
    return buckets[slot]


def assign_and_persist(session: Session, user_id: UUID | str, experiment: str, buckets: Iterable[str] | None = None) -> str:
    if not experiment:
        raise ValueError("experiment name required")

    normalized_id = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    existing = session.exec(
        select(ABTestAssignment).where(
            ABTestAssignment.user_id == normalized_id,
            ABTestAssignment.experiment == experiment,
        )
    ).first()
    if existing:
        return existing.bucket

    bucket = assign(normalized_id, experiment, buckets)
    assignment = ABTestAssignment(user_id=normalized_id, experiment=experiment, bucket=bucket)
    session.add(assignment)
    session.flush()
    return bucket
