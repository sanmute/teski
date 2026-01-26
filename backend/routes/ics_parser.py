# app/backend/routes/import_ics.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlmodel import Session
from db import get_session
from models import Task
from services.ics_parser import parse_ics_text
import httpx

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

    inserted, updated, skipped = upsert_tasks(session, tasks)
    return {"imported": inserted, "updated": updated, "skipped": skipped}

def upsert_tasks(session: Session, tasks: list[dict]):
    inserted = updated = skipped = 0
    for t in tasks:
        if "due_iso" in t and isinstance(t["due_iso"], str):
            from datetime import datetime
            t["due_iso"] = datetime.fromisoformat(t["due_iso"].replace("Z", "+00:00"))
        existing = session.get(Task, t["id"])
        if not existing:
            session.add(Task(**t))
            inserted += 1
        else:
            # Update mutable fields if changed
            changed = False
            for k in ("title","course","due_iso","status","confidence","notes"):
                newv = t.get(k)
                oldv = getattr(existing, k)
                if newv != oldv and newv is not None:
                    setattr(existing, k, newv); changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
    session.commit()
    return inserted, updated, skipped
