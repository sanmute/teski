from __future__ import annotations
from os import getenv
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = ZoneInfo("Europe/Helsinki")

# >>> LEADERBOARD START SETTINGS
TESKI_ANON_SALT = getenv("TESKI_ANON_SALT", "teski-dev-salt")
DEFAULT_TZ = "Europe/Helsinki"
# >>> LEADERBOARD END SETTINGS

# >>> DFE START
TESKI_PARAM_SALT = getenv("TESKI_PARAM_SALT", "teski-dfe-param")
EWMA_ALPHA = float(getenv("TESKI_EWMA_ALPHA", "0.15"))
# <<< DFE END
