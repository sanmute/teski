from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from backend.db import get_session
from backend.models import User


async def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header")
    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
