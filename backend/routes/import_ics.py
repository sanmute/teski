# app/backend/routes/import_ics.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlmodel import Session
from db import get_session
from models import Task
from services.ics_parser import parse_ics_text
from settings import DEFAULT_TIMEZONE
import httpx
import json

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/ics-file")
async def import_ics_file(file: UploadFile = File(...), session: Session = Depends(get_session)):
    content = await file.read()
    try:
        tasks = parse_ics_text(content.decode("utf-8", errors="ignore"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ICS: {e}")

    inserted, updated, skipped = upsert_tasks(session, tasks)
    return {"imported": inserted, "updated": updated, "skipped": skipped}

@router.post("/ics-url")
async def import_ics_url(
    url: str = Query(..., description="Tokenized ICS URL from Moodle 'Get calendar URL'"),
    user_id: str = Query(None),
    session: Session = Depends(get_session),
):

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fetch failed: {e}")
    
    try:
        tasks = parse_ics_text(text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ICS: {e}")

    inserted, updated, skipped = upsert_tasks(session, tasks, owner_user_id=user_id)
    return {"imported": inserted, "updated": updated, "skipped": skipped}

from datetime import datetime
from services.effort import analyze_assignment

UPDATE_FIELDS = {
    "title","course","due_iso","status","confidence","notes","link",
    "task_type","estimated_minutes","suggested_start_utc","signals_json","owner_user_id"
}

def upsert_tasks(session: Session, tasks: list[dict], owner_user_id: str | None = None):
    inserted = updated = skipped = 0
    for t in tasks:
        # ENRICH
        due_value = t["due_iso"]
        if isinstance(due_value, str):
            due_dt = datetime.fromisoformat(due_value.replace("Z", "+00:00"))
        else:
            due_dt = due_value
        if due_dt.tzinfo is None:
            due_local = due_dt.replace(tzinfo=DEFAULT_TIMEZONE)
        else:
            due_local = due_dt.astimezone(DEFAULT_TIMEZONE)
        t["due_iso"] = due_local

        analysis = analyze_assignment(t["title"], t.get("notes",""), due_local, t.get("link"))
        t["task_type"] = analysis["task_type"]
        t["estimated_minutes"] = analysis["estimated_minutes"]
        # store a datetime, not a string (SQLModel handles tz-aware)
        ssu = analysis["suggested_start_utc"]
        if isinstance(ssu, str):
            # just in case your analyzer returns ISO string
            ssu = datetime.fromisoformat(ssu.replace("Z","+00:00"))
        if ssu.tzinfo is None:
            ssu = ssu.replace(tzinfo=DEFAULT_TIMEZONE)
        else:
            ssu = ssu.astimezone(DEFAULT_TIMEZONE)
        t["suggested_start_utc"] = ssu
        t["signals_json"] = json.dumps(analysis["signals"])
        if owner_user_id and not t.get("owner_user_id"):
            t["owner_user_id"] = owner_user_id

        # DEBUG
        # print("[UPSERT] enriched:", t["title"], t["task_type"], t["estimated_minutes"], t["suggested_start_utc"])

        existing = session.get(Task, t["id"])
        if not existing:
            session.add(Task(**{k: v for k, v in t.items() if k in Task.model_fields}))
            inserted += 1
        else:
            changed = False
            for k in UPDATE_FIELDS:
                if k not in t: continue
                newv = t.get(k)
                oldv = getattr(existing, k, None)
                if newv is not None and newv != oldv:
                    setattr(existing, k, newv)
                    changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
    session.commit()
    return inserted, updated, skipped
