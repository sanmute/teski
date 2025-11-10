from __future__ import annotations

import base64
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

PILOT_MODE = os.getenv("PILOT_MODE", "false").lower() in {"1", "true", "yes"}
ADMIN_USER = os.getenv("ADMIN_BASIC_AUTH_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_BASIC_AUTH_PASS", "admin")

_security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(_security)) -> bool:
    """Simple HTTP basic auth guard for pilot admin endpoints."""

    if credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS:
        return True
    raise HTTPException(status_code=401, detail="Unauthorized")


def sign_invite(seed: str) -> str:
    """Derive a deterministic invite code using a salted HMAC."""

    salt = os.getenv("INVITE_CODE_SALT", "teski")
    digest = hmac.new(salt.encode("utf-8"), seed.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")[:10]


def restrict_email(email: str) -> bool:
    """Allow only emails from the configured domain (if any)."""

    domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "").strip().lower()
    if not domain:
        return True
    return email.lower().endswith("@" + domain)
