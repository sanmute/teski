# app/backend/routes/integrations.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import logging, traceback, sys
import sys
from pydantic import BaseModel, AnyHttpUrl, field_validator
from sqlmodel import Session, select
from datetime import datetime, timedelta
import httpx
from db import get_session
from models_integrations import MoodleFeed
from services.ics_parser import parse_ics_text
from routes.import_ics import upsert_tasks  # reuse

logger = logging.getLogger("moodle")

router = APIRouter(prefix="/integrations/moodle", tags=["moodle"])

class SaveMoodleUrlIn(BaseModel):
    user_id: str
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def _require_https(cls, v: AnyHttpUrl):
        if v.scheme != "https":
            raise ValueError("URL must start with https://")
        if len(str(v)) > 2000:
            raise ValueError("URL too long")
        return v

@router.post("/save-url")
async def save_moodle_url(
    payload: SaveMoodleUrlIn | None = Body(default=None),
    url: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    # Prefer JSON body; accept legacy query params for backward compatibility
    if payload:
        url_value = str(payload.url)
        user_value = payload.user_id
    else:
        if not url or not user_id:
            raise HTTPException(status_code=400, detail="user_id and url are required")
        url_value = url
        user_value = user_id

    if not url_value.startswith("https://"):
        raise HTTPException(status_code=400, detail="URL must start with https://")
    if len(url_value) > 2000:
        raise HTTPException(status_code=400, detail="URL too long")

    # Validate link by fetching once
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url_value)
            r.raise_for_status()
            _ = parse_ics_text(r.text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ICS URL or fetch failed: {e}")

    feed = session.exec(select(MoodleFeed).where(MoodleFeed.user_id == user_value)).first()
    if not feed:
        feed = MoodleFeed(user_id=user_value, ics_url=url_value, added_at=datetime.utcnow(), active=True)
        session.add(feed)
    else:
        feed.ics_url = url_value
        feed.added_at = datetime.utcnow()
        feed.active = True
    session.commit()
    return {"ok": True}

@router.post("/refresh-now")
async def refresh_now(
    user_id: str = Query(..., description="UUID of the user requesting refresh"),
    session: Session = Depends(get_session),
):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    logger.info("moodle.refresh-now start", extra={"user_id": user_id})
    try:
        feed = session.exec(
            select(MoodleFeed).where(MoodleFeed.user_id == user_id, MoodleFeed.active == True)
        ).first()
        if not feed:
            logger.info("moodle.refresh-now no_feed", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="No active Moodle feed for this user")

        logger.info("moodle.refresh-now fetch", extra={"user_id": user_id, "ics_url": feed.ics_url})
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                r = await client.get(feed.ics_url)
                r.raise_for_status()
                text = r.text
        except httpx.HTTPStatusError as e:
            logger.warning("moodle.refresh-now fetch_http_error", exc_info=True, extra={"status": e.response.status_code})
            raise HTTPException(status_code=502, detail=f"Fetch failed with status {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning("moodle.refresh-now fetch_request_error", exc_info=True)
            raise HTTPException(status_code=502, detail="Fetch failed: network error")
        except Exception as e:
            logger.warning("moodle.refresh-now fetch_unknown_error", exc_info=True)
            raise HTTPException(status_code=502, detail="Fetch failed")

        try:
            tasks = parse_ics_text(text)
        except Exception as e:
            logger.warning("moodle.refresh-now parse_error", exc_info=True)
            raise HTTPException(status_code=400, detail="Failed to parse ICS")

        try:
            ins, upd, skp = upsert_tasks(session, tasks, owner_user_id=user_id)
        except Exception as e:
            logger.error("moodle.refresh-now import_error", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to import tasks")

        feed.last_fetch_at = datetime.utcnow()
        session.commit()
        logger.info("moodle.refresh-now ok", extra={"user_id": user_id, "imported": ins, "updated": upd, "skipped": skp})
        return {"ok": True, "imported": ins, "updated": upd, "skipped": skp}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        logger.error("moodle.refresh-now internal_error", exc_info=True)
        # Ensure a controlled 500 response without crashing the process.
        return JSONResponse({"ok": False, "error": "internal_error", "detail": str(exc)}, status_code=500)

@router.get("/has-feed")
def has_feed(user_id: str, session: Session = Depends(get_session)):
    feed = session.exec(
        select(MoodleFeed).where(MoodleFeed.user_id == user_id, MoodleFeed.active == True)
    ).first()
    if not feed:
        return {"hasFeed": False, "lastFetchAt": None, "expiresAt": None, "needsRenewal": True}
    expires_at = feed.added_at + timedelta(days=60)
    needs_renewal = datetime.utcnow() >= expires_at
    return {
        "hasFeed": True,
        "lastFetchAt": feed.last_fetch_at,
        "expiresAt": expires_at,
        "needsRenewal": needs_renewal,
    }
