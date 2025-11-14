from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.integrations.ics_parser import parse_ics_text
from app.integrations.models import MoodleFeed, MoodleFeedItem
from app.models import _utcnow
from app.tasks.models import Task
from app.tasks.schemas import TaskCreate
from app.tasks.service import create_task_with_blocks

router = APIRouter(prefix="/api/integrations/moodle", tags=["integrations"])


async def _fetch_ics(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as exc:  # pragma: no cover - network errors surface via HTTP
        raise HTTPException(status_code=400, detail=f"Failed to fetch ICS feed: {exc}") from exc


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user_id") from exc


def _ensure_feed(session: Session, user: UUID) -> MoodleFeed | None:
    return session.exec(
        select(MoodleFeed).where(MoodleFeed.user_id == user, MoodleFeed.active == True)
    ).first()


@router.post("/save-url")
async def save_moodle_url(
    url: str = Query(...),
    user_id: str = Query(...),
    session: Session = Depends(get_session),
):
    user = _parse_user_id(user_id)
    text = await _fetch_ics(url)
    parse_ics_text(text)

    feed = session.exec(select(MoodleFeed).where(MoodleFeed.user_id == user)).first()
    if feed is None:
        feed = MoodleFeed(user_id=user, ics_url=url, added_at=_utcnow(), active=True)
        session.add(feed)
    else:
        feed.ics_url = url
        feed.added_at = _utcnow()
        feed.active = True
    session.commit()
    return {"ok": True}


@router.post("/refresh-now")
async def refresh_now(
    user_id: str = Query(...),
    session: Session = Depends(get_session),
):
    user = _parse_user_id(user_id)
    feed = _ensure_feed(session, user)
    if feed is None:
        raise HTTPException(status_code=404, detail="No active Moodle feed for this user")

    text = await _fetch_ics(feed.ics_url)
    events = parse_ics_text(text)
    created, updated, skipped = _sync_events(session, feed, events)

    feed.last_fetch_at = _utcnow()
    session.add(feed)
    session.commit()
    return {"imported": created, "updated": updated, "skipped": skipped}


@router.get("/has-feed")
def has_feed(
    user_id: str = Query(...),
    session: Session = Depends(get_session),
):
    user = _parse_user_id(user_id)
    feed = _ensure_feed(session, user)
    if feed is None:
        return {"hasFeed": False, "lastFetchAt": None, "expiresAt": None, "needsRenewal": True}
    expires_at = feed.added_at + timedelta(days=60)
    needs_renewal = _utcnow() >= expires_at
    return {
        "hasFeed": True,
        "lastFetchAt": feed.last_fetch_at,
        "expiresAt": expires_at,
        "needsRenewal": needs_renewal,
    }


def _sync_events(session: Session, feed: MoodleFeed, events: List[dict]) -> Tuple[int, int, int]:
    existing_items = session.exec(select(MoodleFeedItem).where(MoodleFeedItem.feed_id == feed.id)).all()
    by_external = {item.external_id: item for item in existing_items}
    created = updated = skipped = 0

    for event in events:
        due_at = _parse_datetime(event.get("due_iso"))
        title = (event.get("title") or "").strip()
        if not due_at or not title:
            skipped += 1
            continue

        external_id = event.get("id") or f"ics_{abs(hash((title, due_at))) }"
        existing = by_external.get(external_id)

        if existing:
            _update_task_from_event(session, existing, event, due_at, title)
            updated += 1
            continue

        payload = TaskCreate(
            title=title,
            course=event.get("course"),
            kind="moodle",
            due_at=due_at,
            base_estimated_minutes=60,
        )
        task, _, _ = create_task_with_blocks(session, feed.user_id, payload)
        item = MoodleFeedItem(
            feed_id=feed.id,
            external_id=external_id,
            task_id=task.id,
            title=title,
            due_at=due_at,
            last_synced_at=_utcnow(),
        )
        session.add(item)
        created += 1

    session.commit()
    return created, updated, skipped


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo:
        return dt
    return dt


def _update_task_from_event(
    session: Session,
    record: MoodleFeedItem,
    event: dict,
    due_at: datetime,
    title: str,
) -> None:
    task = session.get(Task, record.task_id) if record.task_id else None
    if task:
        changed = False
        course = event.get("course")
        if task.title != title:
            task.title = title
            changed = True
        if course and task.course != course:
            task.course = course
            changed = True
        if task.due_at != due_at:
            task.due_at = due_at
            changed = True
        if changed:
            task.updated_at = _utcnow()
            session.add(task)
    record.title = title
    record.due_at = due_at
    record.last_synced_at = _utcnow()
    session.add(record)
