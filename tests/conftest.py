# >>> DFE START
from __future__ import annotations

import sys
from pathlib import Path

import sqlmodel
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


_ORIGINAL_CREATE_ENGINE = sqlmodel.create_engine


def _patched_create_engine(url: str, *args, **kwargs):
    if url.startswith("sqlite://"):
        connect_args = kwargs.setdefault("connect_args", {})
        connect_args.setdefault("check_same_thread", False)
        if "poolclass" not in kwargs:
            kwargs["poolclass"] = StaticPool
    return _ORIGINAL_CREATE_ENGINE(url, *args, **kwargs)


sqlmodel.create_engine = _patched_create_engine
# <<< DFE END
