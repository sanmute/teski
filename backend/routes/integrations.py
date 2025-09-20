# app/backend/routes/integrations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime
import httpx
from ..db import get_session
from ..models_integrations import MoodleFeed
from ..services.ics_parser import parse_ics_text
from ..routes.import_ics import upsert_tasks  # reuse

router = APIRouter(prefix="/api/integrations/moodle", tags=["moodle"])

@router.post("/save-url")
async def save_moodle_url(
    url: str = Query(...),
    user_id: str = Query(...),
    session: Session = Depends(get_session),
):
    # Validate link by fetching once
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            _ = parse_ics_text(r.text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ICS URL or fetch failed: {e}")

    feed = session.exec(select(MoodleFeed).where(MoodleFeed.user_id == user_id)).first()
    if not feed:
        feed = MoodleFeed(user_id=user_id, ics_url=url, added_at=datetime.utcnow(), active=True)
        session.add(feed)
    else:
        feed.ics_url = url
        feed.added_at = datetime.utcnow()
        feed.active = True
    session.commit()
    return {"ok": True}

@router.post("/refresh-now")
async def refresh_now(
    user_id: str = Query(...),
    session: Session = Depends(get_session),
):
    feed = session.exec(
        select(MoodleFeed).where(MoodleFeed.user_id == user_id, MoodleFeed.active == True)
    ).first()
    if not feed:
        raise HTTPException(status_code=404, detail="No active Moodle feed for this user")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(feed.ics_url)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fetch failed: {e}")

    tasks = parse_ics_text(text)
    ins, upd, skp = upsert_tasks(session, tasks, owner_user_id=user_id)
    feed.last_fetch_at = datetime.utcnow()
    session.commit()
    return {"imported": ins, "updated": upd, "skipped": skp}

@router.get("/has-feed")
def has_feed(user_id: str, session: Session = Depends(get_session)):
    feed = session.exec(select(MoodleFeed).where(MoodleFeed.user_id == user_id, MoodleFeed.active==True)).first()
    return {"hasFeed": bool(feed), "lastFetchAt": feed.last_fetch_at if feed else None}
