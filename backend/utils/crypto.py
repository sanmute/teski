# >>> LEADERBOARD START CRYPTO
"""Crypto helpers for anonymised leaderboard handles."""

from __future__ import annotations

import base64
import hmac
import hashlib

from os import getenv

from backend.core.leaderboard_constants import HASH_SALT_ENV
from backend.settings import TESKI_ANON_SALT


def _salt_value() -> str:
    return getenv(HASH_SALT_ENV, TESKI_ANON_SALT)


def anon_handle(user_id: int, email: str, salt: str | None = None) -> str:
    """Return a stable anonymous handle derived from user id and email."""

    effective_salt = salt or _salt_value()
    digest = hmac.new(
        effective_salt.encode("utf-8"),
        f"{user_id}:{email}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    encoded = base64.b32encode(digest).decode("utf-8").rstrip("=")
    return f"an_{encoded[:10]}"
# >>> LEADERBOARD END CRYPTO
