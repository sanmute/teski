# app/backend/services/ics_parser.py
from __future__ import annotations
from ics import Calendar
import re
from typing import List, Dict, Any
from ..settings import DEFAULT_TIMEZONE

DUE_RE = re.compile(r'\b(due|deadline|closes?|submission|submit|DL)\b', re.I)

def parse_ics_text(text: str, default_tz=DEFAULT_TIMEZONE) -> List[Dict[str, Any]]:
    cal = Calendar(text)
    tasks = []
    for ev in cal.events:
        title = (ev.name or "").strip()
        desc = (ev.description or "")
        text_block = f"{title}\n{desc}"

        # Only keep events that look like deadlines/submissions
        if not DUE_RE.search(text_block):
            continue

        # Prefer END as the “closes” moment; fallback to BEGIN
        dt = (ev.end or ev.begin)
        if not dt:
            continue
        if dt.tzinfo is None:
            due_local = dt.replace(tzinfo=default_tz)
        else:
            due_local = dt.astimezone(default_tz)

        # Try ICS UID, else hash(title,due)
        uid = getattr(ev, "uid", None)
        if not uid:
            uid = f"ics_{abs(hash((title, due_local.isoformat())))}"

        tasks.append({
            "id": uid,
            "source": "ics",
            "title": title or "Moodle Deadline",
            "course": extract_course(title, desc),
            "due_iso": due_local.isoformat(),
            "status": "open",
            "confidence": 0.9 if DUE_RE.search(title) else 0.8,
            "notes": desc[:500] if desc else None,
        })
    return tasks

def extract_course(title: str, desc: str | None = None) -> str | None:
    # Try formats like [MATH201], MATH-201, CS101 etc.
    import re
    for pat in (r'\[([A-Z]{2,5}[- ]?\d{2,4})\]', r'\b([A-Z]{2,5}[- ]?\d{2,4})\b'):
        m = re.search(pat, title)
        if m: return m.group(1)
    if desc:
        m = re.search(r'\b([A-Z]{2,5}[- ]?\d{2,4})\b', desc)
        if m: return m.group(1)
    return None
