# >>> ANALYTICS START
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

log = logging.getLogger("analytics")


def emit(event: str, user_id: int, props: Dict[str, Any] | None = None) -> None:
    payload = {
        "event": event,
        "user_id": user_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "props": props or {},
    }
    log.info("[analytics] %s", payload)
# <<< ANALYTICS END
