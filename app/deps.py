from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.models import User


async def get_current_user(
    x_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header")
    user = session.get(User, x_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
