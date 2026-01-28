from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query

router = APIRouter(prefix="/ex", tags=["exercises"])


@router.get("/list")
def list_exercises_alias(
    user_id: Optional[UUID] = Query(default=None, description="User requesting exercises"),
    difficulty_min: int = Query(default=1, ge=1, description="Ignored in fallback"),
    difficulty_max: int = Query(default=5, ge=1, description="Ignored in fallback"),
) -> Dict[str, Any]:
    """
    Compatibility endpoint for /api/ex/list when the optional app.ex_api package
    is unavailable. Shape matches the frontend expectation: an object with
    'items', 'page', 'page_size', and 'total' keys.
    """
    try:
        # Delegate to the richer implementation if available.
        from app import ex_api as app_ex_api

        print("[ex_alias] Delegating to app.ex_api.list_exercises", file=sys.stderr)
        return app_ex_api.list_exercises()  # type: ignore[return-value]
    except Exception as exc:
        print(f"[ex_alias] Fallback list_exercises: {exc}", file=sys.stderr)

    # Minimal fallback: return an empty list but keep schema stable.
    return {"items": [], "page": 1, "page_size": 0, "total": 0}

