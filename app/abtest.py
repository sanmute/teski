from __future__ import annotations

import hashlib
from typing import Any, Iterable, List

from app.config import get_settings


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
