from __future__ import annotations

import re
from typing import Any, Dict, List

from ics import Calendar

DUE_RE = re.compile(r"\b(due|deadline|closes?|submission|submit|DL)\b", re.I)


def parse_ics_text(text: str) -> List[Dict[str, Any]]:
    cal = Calendar(text)
    tasks: List[Dict[str, Any]] = []
    for ev in cal.events:
        title = (ev.name or "").strip()
        desc = (ev.description or "")
        text_block = f"{title}\n{desc}"

        if not DUE_RE.search(text_block):
            continue

        dt = (ev.end or ev.begin)
        if not dt:
            continue
        due_local = dt if dt.tzinfo else dt.replace(tzinfo=None)

        uid = getattr(ev, "uid", None)
        if not uid:
            uid = f"ics_{abs(hash((title, due_local.isoformat())))}"

        tasks.append(
            {
                "id": uid,
                "title": title or "Moodle Deadline",
                "course": _extract_course(title, desc),
                "due_iso": due_local.isoformat(),
                "notes": desc[:500] if desc else None,
            }
        )
    return tasks


def _extract_course(title: str, desc: str | None = None) -> str | None:
    for pat in (r"\[([A-Z]{2,5}[- ]?\d{2,4})\]", r"\b([A-Z]{2,5}[- ]?\d{2,4})\b"):
        match = re.search(pat, title)
        if match:
            return match.group(1)
    if desc:
        match = re.search(r"\b([A-Z]{2,5}[- ]?\d{2,4})\b", desc)
        if match:
            return match.group(1)
    return None
