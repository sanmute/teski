from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, select, func

from ..db import get_session
from ..deep.models import SelfExplanation
from ..models import User
from .models import PilotConsent, PilotFeedback, PilotInvite, PilotSession
from .utils import PILOT_MODE, require_admin, restrict_email, sign_invite

try:
    from ..feedback.costs import get_cost_stats
except Exception:  # pragma: no cover - fallback when costs module missing
    def get_cost_stats(session: Session) -> Dict[str, Any]:
        return {
            "cost_total_eur": 0.0,
            "cost_last_30d_eur": 0.0,
            "events_total": 0,
            "cache_hit_rate": 0.0,
        }


router = APIRouter(prefix="/pilot", tags=["pilot"])


def _ensure_pilot_mode() -> None:
    if not PILOT_MODE:
        raise HTTPException(status_code=400, detail="Pilot mode disabled")


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:  # pragma: no cover - validation
        raise HTTPException(status_code=400, detail="Invalid user_id") from exc


def _get_or_create_user(session: Session, email: str) -> User:
    row = session.exec(select(User).where(User.display_name == email)).first()
    if row:
        return row
    user = User(display_name=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _pilot_name() -> str:
    return os.getenv("PILOT_NAME", "Teski Pilot")


@router.post("/invites/create", dependencies=[Depends(require_admin)])
def create_invites(
    count: int = Body(10),
    email_hint: Optional[str] = Body(None),
    session: Session = Depends(get_session),
):
    codes: List[str] = []
    for idx in range(max(1, count)):
        seed = f"{email_hint or 'user'}-{datetime.utcnow().isoformat()}-{idx}"
        code = sign_invite(seed)
        session.add(PilotInvite(code=code, email_hint=email_hint))
        codes.append(code)
    session.commit()
    return {"codes": codes}


@router.post("/signup")
def signup_with_invite(
    email: str = Body(..., embed=True),
    code: str = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    _ensure_pilot_mode()
    if not restrict_email(email):
        raise HTTPException(status_code=403, detail="Email domain not allowed for this pilot")

    invite = session.exec(select(PilotInvite).where(PilotInvite.code == code)).first()
    if not invite or invite.used_by_user is not None:
        raise HTTPException(status_code=403, detail="Invalid or used invite code")

    user = _get_or_create_user(session, email=email)
    invite.used_by_user = user.id
    invite.used_at = datetime.utcnow()
    session.add(invite)
    session.commit()

    return {"user_id": str(user.id), "message": "Invite accepted. Continue to consent."}


@router.post("/consent/accept")
def consent_accept(
    user_id: str = Body(..., embed=True),
    text_version: str = Body("v1", embed=True),
    session: Session = Depends(get_session),
):
    _ensure_pilot_mode()
    uuid = _parse_uuid(user_id)
    consent = session.exec(select(PilotConsent).where(PilotConsent.user_id == uuid)).first()
    if not consent:
        consent = PilotConsent(user_id=uuid)
    consent.accepted = True
    consent.text_version = text_version
    consent.accepted_at = datetime.utcnow()
    session.add(consent)
    session.commit()
    return {"status": "ok"}


@router.get("/consent/status")
def consent_status(user_id: str, session: Session = Depends(get_session)):
    uuid = _parse_uuid(user_id)
    row = session.exec(select(PilotConsent).where(PilotConsent.user_id == uuid)).first()
    return {
        "accepted": bool(row and row.accepted),
        "text_version": row.text_version if row else None,
    }


@router.post("/session/start")
def session_start(
    user_id: str = Body(..., embed=True),
    topic_id: Optional[str] = Body(None, embed=True),
    session: Session = Depends(get_session),
):
    _ensure_pilot_mode()
    uuid = _parse_uuid(user_id)
    pilot_session = PilotSession(user_id=uuid, topic_id=topic_id)
    session.add(pilot_session)
    session.commit()
    session.refresh(pilot_session)
    return {"session_id": pilot_session.id}


@router.post("/session/end")
def session_end(
    session_id: int = Body(..., embed=True),
    minutes_active: int = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    _ensure_pilot_mode()
    row = session.get(PilotSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.ended_at = datetime.utcnow()
    row.minutes_active = max(0, minutes_active)
    session.add(row)
    session.commit()
    return {"status": "ok"}


@router.post("/feedback")
def leave_feedback(
    message: str = Body(..., embed=True),
    user_id: Optional[str] = Body(None, embed=True),
    context_json: Dict[str, Any] = Body(default_factory=dict, embed=True),
    session: Session = Depends(get_session),
):
    uuid = _parse_uuid(user_id) if user_id else None
    feedback = PilotFeedback(user_id=uuid, message=message, context_json=context_json)
    session.add(feedback)
    session.commit()
    session.refresh(feedback)

    webhook_url = os.getenv("MAIL_WEBHOOK_URL", "").strip()
    if webhook_url:
        payload = {
            "text": (
                f"Teski Pilot Feedback ({_pilot_name()}): {message}\n"
                f"User: {user_id or '-'}\nContext: {json.dumps(context_json)[:500]}"
            )
        }
        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(webhook_url, json=payload)
        except Exception:
            # Slack/webhook failures should not break UX
            pass

    return {"status": "ok", "id": feedback.id}


@router.get("/admin/overview", dependencies=[Depends(require_admin)])
def admin_overview(session: Session = Depends(get_session)):
    users_total = (
        session.exec(
            select(func.count()).select_from(PilotInvite).where(PilotInvite.used_by_user.is_not(None))
        ).one()
        or 0
    )
    sessions_total = session.exec(select(func.count()).select_from(PilotSession)).one() or 0
    consents = (
        session.exec(
            select(func.count()).select_from(PilotConsent).where(PilotConsent.accepted.is_(True))
        ).one()
        or 0
    )
    depth_avg = session.exec(select(func.avg(SelfExplanation.score_deep))).one() or 0.0
    costs = get_cost_stats(session)
    return {
        "users_total": int(users_total),
        "sessions_total": int(sessions_total),
        "consents": int(consents),
        "depth_avg": float(depth_avg or 0.0),
        "costs": costs,
    }


@router.get("/admin/users", dependencies=[Depends(require_admin)])
def admin_users(session: Session = Depends(get_session)):
    rows = session.exec(select(PilotInvite).where(PilotInvite.used_by_user.is_not(None))).all()
    return [
        {
            "code": row.code,
            "user_id": str(row.used_by_user),
            "email_hint": row.email_hint,
            "used_at": row.used_at.isoformat() if row.used_at else None,
        }
        for row in rows
    ]


@router.get("/admin/sessions", dependencies=[Depends(require_admin)])
def admin_sessions(limit: int = 100, session: Session = Depends(get_session)):
    rows = (
        session.exec(select(PilotSession).order_by(PilotSession.started_at.desc()).limit(limit)).all()
    )
    return [
        {
            "id": row.id,
            "user_id": str(row.user_id),
            "topic_id": row.topic_id,
            "minutes_active": row.minutes_active,
            "started_at": row.started_at.isoformat(),
            "ended_at": row.ended_at.isoformat() if row.ended_at else None,
        }
        for row in rows
    ]


@router.get("/admin/depth", dependencies=[Depends(require_admin)])
def admin_depth(limit: int = 100, session: Session = Depends(get_session)):
    rows = (
        session.exec(select(SelfExplanation).order_by(SelfExplanation.created_at.desc()).limit(limit)).all()
    )
    return [
        {
            "user_id": str(row.user_id),
            "topic_id": row.topic_id,
            "score": row.score_deep,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/admin/report", dependencies=[Depends(require_admin)])
def admin_report(session: Session = Depends(get_session)):
    users_total = (
        session.exec(
            select(func.count()).select_from(PilotInvite).where(PilotInvite.used_by_user.is_not(None))
        ).one()
        or 0
    )
    consents = (
        session.exec(
            select(func.count()).select_from(PilotConsent).where(PilotConsent.accepted.is_(True))
        ).one()
        or 0
    )
    sessions_total = session.exec(select(func.count()).select_from(PilotSession)).one() or 0
    depth_avg = session.exec(select(func.avg(SelfExplanation.score_deep))).one() or 0.0

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["session_id", "user_id", "topic_id", "minutes_active", "started_at", "ended_at"])
    for row in session.exec(select(PilotSession).order_by(PilotSession.started_at.asc())).all():
        writer.writerow(
            [
                row.id,
                row.user_id,
                row.topic_id or "",
                row.minutes_active,
                row.started_at.isoformat(),
                row.ended_at.isoformat() if row.ended_at else "",
            ]
        )

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "pilot_name": _pilot_name(),
        "kpis": {
            "users_total": int(users_total),
            "consents": int(consents),
            "sessions_total": int(sessions_total),
            "avg_depth_score": float(depth_avg or 0.0),
        },
    }
    return {"csv": stream.getvalue(), "summary": report}
