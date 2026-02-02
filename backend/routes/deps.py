from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status, Query, Request
import logging
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError
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
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    user_id_q: str | None = Query(default=None, alias="user_id"),
    session: Session = Depends(get_session),
) -> User:
    if request.method.upper() == "OPTIONS":
        logger.debug("auth skip OPTIONS", extra={"path": request.url.path, "origin": request.headers.get("origin")})
        # Return a lightweight placeholder user to satisfy dependency chain for CORS preflight
        return User(id=0, external_user_id="options-preflight", email="options@teski.app", hashed_password="")
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
        except ExpiredSignatureError as e:
            reason = "expired"
            try:
                logger.warning(
                    "auth.decode_failed",
                    extra={"err": type(e).__name__, "err_msg": str(e), "alg": settings.ALGORITHM},
                )
            except KeyError:
                logger.warning("auth.decode_failed")
            if request.headers.get("x-teski-debug") == "trace":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "Could not validate credentials", "reason": reason},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise credentials_exception
        except JWTClaimsError as e:
            # Audience / issuer errors fall here
            err_type = type(e).__name__
            if "audience" in err_type.lower():
                reason = "wrong_audience"
            elif "issuer" in err_type.lower():
                reason = "wrong_issuer"
            else:
                reason = f"decode_error:{err_type}"
            try:
                logger.warning(
                    "auth.decode_failed",
                    extra={"err": err_type, "err_msg": str(e), "alg": settings.ALGORITHM},
                )
            except KeyError:
                logger.warning("auth.decode_failed")
            if request.headers.get("x-teski-debug") == "trace":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "Could not validate credentials", "reason": reason},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise credentials_exception
        except JWTError as e:
            try:
                logger.warning(
                    "auth.decode_failed",
                    extra={"err": type(e).__name__, "err_msg": str(e), "alg": settings.ALGORITHM},
                )
            except KeyError:
                logger.warning("auth.decode_failed")
            if request.headers.get("x-teski-debug") == "trace":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "Could not validate credentials", "reason": f"decode_error:{type(e).__name__}"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
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
        if request.headers.get("x-teski-debug") == "trace":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "User not found", "reason": "user_not_found"})
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
