from __future__ import annotations

import json
import os
import traceback
from typing import Optional, Literal, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session, SQLModel, select

from db import get_session
from models import User
from models_feedback import FeedbackItem
from routes.deps import get_current_user, oauth2_scheme
from security import decode_access_token
from jose import JWTError
from services.emailer import send_feedback_email, DISABLED_REASON

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackIn(SQLModel):
    kind: Literal["feedback", "bug", "idea"] = "feedback"
    message: str
    severity: Optional[Literal["low", "medium", "high"]] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    app_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _get_admin_emails() -> set[str]:
    raw = os.getenv("TESKI_ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    admin_emails = _get_admin_emails()
    if not admin_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin emails not configured")
    if current_user.email.lower() not in admin_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return current_user


async def get_optional_user(token: str | None = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> Optional[User]:
    """Best-effort user resolution. Returns None if unauthenticated/invalid."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            return None
        # get_current_user expects integer primary key
        try:
            user_int = int(sub)
        except (TypeError, ValueError):
            return None
        return session.get(User, user_int)
    except JWTError:
        return None


@router.post("/submit")
async def submit_feedback(
    payload: FeedbackIn,
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if not payload.message or len(payload.message.strip()) < 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message too short")

    item = FeedbackItem(
        kind=payload.kind,
        message=payload.message.strip(),
        severity=payload.severity,
        page_url=payload.page_url,
        user_agent=payload.user_agent or request.headers.get("user-agent"),
        app_version=payload.app_version,
        metadata_json=payload.metadata or {},
        user_id=current_user.external_user_id if current_user else None,
        user_email=current_user.email if current_user else None,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    # Best-effort email notify
    try:
        subject = f"[Teski Feedback] {item.kind}/{item.severity or '-'} from {item.user_email or item.user_id or 'anon'}"
        body = "\n".join(
            [
                f"Kind: {item.kind}",
                f"Severity: {item.severity or '-'}",
                f"Message: {item.message}",
                f"User: {item.user_email or item.user_id or 'anonymous'}",
                f"Page: {item.page_url or '-'}",
                f"User-Agent: {item.user_agent or '-'}",
                f"App version: {item.app_version or '-'}",
                f"Metadata: {json.dumps(item.metadata_json) if item.metadata_json else '{}'}",
                f"Created: {item.created_at.isoformat()}",
                f"Email mode: {'disabled' if DISABLED_REASON else 'enabled'}",
            ]
        )
        send_feedback_email(subject, body)
    except Exception:
        traceback.print_exc()

    return {"ok": True, "id": item.id}


@router.get("/list")
def list_feedback(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    kind: Optional[str] = None,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin_user),
):
    stmt = select(FeedbackItem)
    if kind:
        stmt = stmt.where(FeedbackItem.kind == kind)
    all_ids = session.exec(stmt).all()
    total = len(all_ids)
    items = session.exec(stmt.order_by(FeedbackItem.created_at.desc()).offset(offset).limit(limit)).all()
    return {"ok": True, "items": items, "total": total}


@router.get("/get")
def get_feedback(
    id: int = Query(...),
    session: Session = Depends(get_session),
    _: User = Depends(require_admin_user),
):
    item = session.get(FeedbackItem, id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"ok": True, "item": item}
