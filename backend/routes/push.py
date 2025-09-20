# app/backend/routes/push.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from os import getenv
from pywebpush import webpush, WebPushException
import json
from ..db import get_session
from ..models_push import PushSubscription

router = APIRouter(prefix="/api/push", tags=["push"])

VAPID_PUBLIC_KEY = getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_PEM = getenv("VAPID_PRIVATE_PEM")

@router.get("/vapid-public-key")
def vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(500, "VAPID public key not configured")
    return {"publicKey": VAPID_PUBLIC_KEY}

@router.post("/register")
async def register_push(body: dict, session: Session = Depends(get_session)):
    """
    body = {
      "user_id": "clientId-uuid",
      "subscription": { endpoint, keys: {p256dh, auth} },
      "platform": "web"
    }
    """
    try:
        user_id = body["user_id"]
        sub = body["subscription"]
        endpoint = sub["endpoint"]
        p256dh = sub["keys"]["p256dh"]
        auth = sub["keys"]["auth"]
    except KeyError:
        raise HTTPException(400, "Invalid subscription payload")

    existing = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    ).first()
    if existing:
        existing.user_id = user_id
        existing.p256dh = p256dh
        existing.auth = auth
        existing.platform = body.get("platform", "web")
        existing.active = True
    else:
        session.add(PushSubscription(
            user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth,
            platform=body.get("platform","web"), active=True
        ))
    session.commit()
    return {"ok": True}

@router.post("/unregister")
async def unregister_push(body: dict, session: Session = Depends(get_session)):
    """
    body = { "endpoint": "<endpoint>" }  # or pass user_id to disable all
    """
    endpoint = body.get("endpoint")
    user_id = body.get("user_id")
    if endpoint:
        session.exec(delete(PushSubscription).where(PushSubscription.endpoint == endpoint))
    elif user_id:
        subs = session.exec(select(PushSubscription).where(PushSubscription.user_id == user_id)).all()
        for s in subs: s.active = False
        session.commit()
    else:
        raise HTTPException(400, "Provide endpoint or user_id")
    session.commit()
    return {"ok": True}

def send_web_push(subscription: PushSubscription, payload: dict):
    if not VAPID_PRIVATE_PEM or not VAPID_PUBLIC_KEY:
        raise RuntimeError("VAPID keys not configured")
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_PEM,
            vapid_claims={"sub": "mailto:admin@teski.app"},
        )
        return True
    except WebPushException as e:
        # 404/410 → endpoint expired: remove it
        if e.response and e.response.status_code in (404, 410):
            subscription.active = False
        return False

@router.post("/test")
def test_push(user_id: str, session: Session = Depends(get_session)):
    subs = session.exec(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id, PushSubscription.active == True
        )
    ).all()
    if not subs:
        raise HTTPException(404, "No active subscriptions for user")
    ok = 0
    for s in subs:
        if send_web_push(s, {
            "title": "Teski",
            "body": "This is a test nudge. Breathe in, then go do the thing.",
            "taskId": None,
            "collapseId": "test"  # dedupe on SW side
        }):
            ok += 1
    session.commit()
    return {"sent": ok, "total": len(subs)}
