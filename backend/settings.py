from __future__ import annotations
from os import getenv
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = ZoneInfo("Europe/Helsinki")

# >>> LEADERBOARD START SETTINGS
TESKI_ANON_SALT = getenv("TESKI_ANON_SALT", "teski-dev-salt")
DEFAULT_TZ = "Europe/Helsinki"
# >>> LEADERBOARD END SETTINGS
