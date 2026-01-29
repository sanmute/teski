from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, select

import settings
from db import get_session
from models import User
from security import create_access_token, hash_password, verify_password
from routes.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(SQLModel):
    email: str
    password: str
    display_name: Optional[str] = None


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class LoginRequest(SQLModel):
    email: str
    password: str


@router.post("/signup", response_model=TokenResponse)
def signup(
    payload: SignupRequest,
    session: Session = Depends(get_session),
):
    email_normalized = payload.email.strip().lower()
    existing = session.exec(select(User).where(User.email == email_normalized)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=email_normalized,
        display_name=payload.display_name,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires_delta)
    return TokenResponse(access_token=access_token, user_id=user.external_user_id, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    email_normalized = form_data.username.strip().lower()
    user = session.exec(select(User).where(User.email == email_normalized)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires_delta)
    return TokenResponse(access_token=access_token, user_id=user.external_user_id, email=user.email)


@router.post("/login-json", response_model=TokenResponse)
def login_json(
    payload: LoginRequest,
    session: Session = Depends(get_session),
):
    email_normalized = payload.email.strip().lower()
    user = session.exec(select(User).where(User.email == email_normalized)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires_delta)
    return TokenResponse(access_token=access_token, user_id=user.external_user_id, email=user.email)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "ok": True,
        "user_id": current_user.external_user_id,
        "email": current_user.email,
    }
