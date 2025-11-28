from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

from backend import settings
from backend.db import get_session
from backend.models import User, UserRole
from backend.models_institution import Course
from backend.security import decode_access_token
from backend.services.authorization import user_can_edit_course

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
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
        except JWTError:
            raise credentials_exception
    elif x_user_id is not None:
        user_id = x_user_id

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header")

    user = session.get(User, int(user_id))
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
