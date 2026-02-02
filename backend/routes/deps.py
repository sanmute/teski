from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status, Query
import logging
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

import settings
from db import get_session
from models import User, UserRole
from models_institution import Course
from security import decode_access_token
from services.authorization import user_can_edit_course

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


logger = logging.getLogger("auth")


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    user_id_q: str | None = Query(default=None, alias="user_id"),
    session: Session = Depends(get_session),
) -> User:
    user_id = None
    if token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError as e:
            logger.warning("auth.decode_failed", extra={"err": type(e).__name__, "msg": str(e), "alg": settings.ALGORITHM})
            raise credentials_exception
    elif x_user_id is not None:
        user_id = x_user_id
    elif user_id_q is not None:
        user_id = user_id_q

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header")

    # If both header and query were provided, ensure they match to avoid spoofing.
    if x_user_id is not None and user_id_q is not None and x_user_id != user_id_q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id mismatch")

    try:
        user_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id must be an integer")

    user = session.get(User, user_int)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_teski_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.TESKI_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TESKI_ADMIN role required",
        )
    return current_user


def require_educator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.EDUCATOR, UserRole.INSTITUTION_ADMIN, UserRole.TESKI_ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Educator role required",
        )
    return current_user


def require_course_editor(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    if not user_can_edit_course(current_user, course, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to edit this course",
        )
    return course
