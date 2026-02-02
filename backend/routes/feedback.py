from __future__ import annotations

import json
import os
import traceback
from typing import Optional, Literal, Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session, SQLModel, select, Field

from db import get_session
from models import User
from models_feedback import FeedbackItem
from routes.deps import get_current_user, oauth2_scheme
from security import decode_access_token
from jose import JWTError
from services.emailer import send_feedback_email, DISABLED_REASON

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


class FeedbackIn(SQLModel):
    kind: Literal["feedback", "bug", "idea"] = "feedback"
    message: str
    severity: Optional[Literal["low", "medium", "high"]] = None
    page_url: Optional[str] = Field(default=None, alias="page")
    user_agent: Optional[str] = None
    app_version: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    raffle_opt_in: bool = False
    raffle_name: Optional[str] = None
    raffle_email: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "ignore"


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

    raffle_opt_in = bool(payload.raffle_opt_in)
    raffle_name = payload.raffle_name.strip() if (payload.raffle_name and raffle_opt_in) else None
    raffle_email = payload.raffle_email.strip() if (payload.raffle_email and raffle_opt_in) else None

    if raffle_opt_in and not raffle_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required to join the raffle")

    page_url = payload.page_url or request.headers.get("referer") or request.headers.get("origin") or "(unknown)"
    app_version = payload.app_version or "(unknown)"

    raw_metadata = payload.metadata_json
    if raw_metadata is None:
        metadata: Dict[str, Any] = {}
    elif isinstance(raw_metadata, dict):
        metadata = raw_metadata
    else:
        try:
            metadata = json.loads(raw_metadata)
        except Exception:
            metadata = {}

    item = FeedbackItem(
        kind=payload.kind,
        message=payload.message.strip(),
        severity=payload.severity,
        page_url=page_url,
        user_agent=payload.user_agent or request.headers.get("user-agent"),
        app_version=app_version,
        metadata_json=metadata,
        user_id=current_user.external_user_id if current_user else None,
        user_email=current_user.email if current_user else None,
        raffle_opt_in=raffle_opt_in,
        raffle_name=raffle_name,
        raffle_email=raffle_email,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info(
        "feedback_submit id=%s user=%s page=%s app_version=%s raffle=%s",
        item.id,
        item.user_id or item.user_email or "anon",
        item.page_url,
        item.app_version,
        item.raffle_opt_in,
    )

    # Best-effort email notify
    try:
        metadata = item.metadata_json or {}
        viewport = metadata.get("viewport") or {}
        viewport_str = (
            f"{viewport.get('w')}x{viewport.get('h')} dpr {viewport.get('dpr')}"
            if viewport
            else "-"
        )
        timestamp_iso = metadata.get("timestamp_iso") or item.created_at.isoformat()
        referrer = metadata.get("referrer") or "-"
        timezone = metadata.get("timezone") or "-"

        subject = f"[Teski Feedback] {item.kind}/{item.severity or '-'} from {item.user_email or item.user_id or 'anon'}"
        body = "\n".join(
            [
                f"Kind: {item.kind}",
                f"Severity: {item.severity or '-'}",
                f"Message: {item.message}",
                f"User: {item.user_email or item.user_id or 'anonymous'}",
                "Context:",
                f"  Page: {item.page_url or '-'}",
                f"  App version: {item.app_version or '(unknown)'}",
                f"  Timestamp: {timestamp_iso}",
                f"  Browser: {metadata.get('user_agent') or item.user_agent or '-'}",
                f"  Timezone: {timezone}",
                f"  Viewport: {viewport_str}",
                f"  Referrer: {referrer}",
                f"  Raw metadata: {json.dumps(item.metadata_json) if item.metadata_json else '{}'}",
                "---",
                f"Raffle opt-in: {'Yes' if item.raffle_opt_in else 'No'}",
                *( [f"Name: {item.raffle_name}"] if item.raffle_opt_in and item.raffle_name else [] ),
                *(
                    [
                        "Contact: "
                        + (
                            item.raffle_email
                            or item.user_email
                            or "(not provided)"
                        )
                    ]
                    if item.raffle_opt_in
                    else []
                ),
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
