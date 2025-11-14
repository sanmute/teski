from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import User


settings = get_settings()


async def get_current_user(
    x_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header")

    user = session.get(User, x_user_id)
    if user is None:
        user = User(id=x_user_id, persona=settings.PERSONA_DEFAULT)
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
