# >>> LEADERBOARD START CODES
"""Join code helpers."""

from __future__ import annotations

import secrets

from core.leaderboard_constants import JOIN_CODE_ALPHABET, JOIN_CODE_LENGTH


def generate_join_code() -> str:
    """Generate a random leaderboard join code."""

    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(JOIN_CODE_LENGTH))
# >>> LEADERBOARD END CODES
