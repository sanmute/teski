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

# >>> MEMORY START
class MemorySettings:
    DECAY_HALF_LIFE_DAYS: float = float(getenv("TESKI_MEMORY_HALFLIFE_DAYS", "7.0"))
    MEMORY_V2_DUAL_WRITE: bool = getenv("TESKI_MEMORY_V2_DUAL_WRITE", "false").lower() == "true"


memory_settings = MemorySettings()
# <<< MEMORY END

# >>> MEMORY V1 START
class MemoryV1Settings:
    DEFAULT_EASINESS: float = float(getenv("TESKI_SRS_EASINESS", "2.3"))
    MAX_WARMUP_ITEMS: int = int(getenv("TESKI_WARMUP_MAX", "2"))
    DAILY_REVIEW_CAP: int = int(getenv("TESKI_SRS_DAILY_CAP", "6"))
    QUEUE_BACKOFF_THRESHOLD: int = int(getenv("TESKI_SRS_QUEUE_BACKOFF", "20"))
    DISABLE_MEMORY_V1: bool = getenv("TESKI_MEMORY_DISABLE", "false").lower() == "true"


memory_v1_settings = MemoryV1Settings()
# <<< MEMORY V1 END

# >>> AUTH START
# Prefer SECRET_KEY (used in existing .env.backend) and fall back to TESKI_SECRET_KEY.
_secret_env = getenv("SECRET_KEY") or getenv("TESKI_SECRET_KEY")
SECRET_KEY = _secret_env or "change-me-in-prod"
ALGORITHM = getenv("TESKI_JWT_ALG", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("TESKI_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
# <<< AUTH END
