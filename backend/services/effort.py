# app/backend/services/effort.py
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from settings import DEFAULT_TIMEZONE

# 1) Keyword maps for coarse classification
# Order matters: more specific patterns should come first.
TYPE_PATTERNS = [
    ("coding",        r"\b(code|coding|program|script|algorithm|implementation|repository|github|notebook)\b"),
    ("data_analysis", r"\b(data analysis|dataset|regression|analy(s|z)e|tableau|visuali(s|z)ation|spreadsheet)\b"),
    ("design_doc",    r"\b(design doc|design brief|requirements spec|architecture|system design)\b"),
    ("proposal",      r"\b(proposal|prospectus|research plan|pitch deck)\b"),
    ("essay",         r"\b(essay|reflection|opinion piece|literature review)\b"),
    ("report",        r"\b(report|case study|write[- ]up|whitepaper)\b"),
    ("exercise",      r"\b(exercise(?:\s*\d+)?|practice exercise|weekly exercise)\b"),
    ("problem_set",   r"\b(problem set|pset|homework|exercises|assignment\s*\d+)\b"),
    ("worksheet",     r"\b(worksheet|practice sheet|drill)\b"),
    ("quiz",          r"\b(quiz|mcq|short test)\b"),
    ("exam",          r"\b(exam|midterm|final|test)\b"),
    ("lab",           r"\b(lab|practic(al|e)|experiment)\b"),
    ("reading",       r"\b(reading|chapters?\s*\d+|article review|close reading)\b"),
    ("presentation",  r"\b(presentation|speech|pitch|slides|deck|talk|poster)\b"),
    ("discussion",    r"\b(discussion|forum post|peer response|comment)\b"),
    ("project",       r"\b(project|capstone|prototype|build|sprint|milestone)\b"),
    ("peer_review",   r"\b(peer review|review a peer|feedback)\b"),
]

# 2) Baseline minutes by type (starter heuristics)
BASELINE_MIN = {
    "essay": 240,         # 4h (research+draft)
    "report": 300,        # 5h
    "proposal": 180,
    "design_doc": 240,
    "problem_set": 180,   # 3h
    "exercise": 120,
    "worksheet": 90,
    "quiz": 45,           # 45m
    "exam": 120,          # 2h study (excl. test time)
    "lab": 180,
    "reading": 90,
    "presentation": 180,
    "discussion": 40,
    "project": 420,       # 7h (MVP chunk)
    "coding": 240,
    "data_analysis": 210,
    "peer_review": 60,
    "unknown": 90,
}

WORDS_RE = re.compile(r"\b(\d{2,5})\s*(words?|wds?)\b", re.I)
PAGES_RE = re.compile(r"\b(\d{1,3})\s*(pages?|pgs?)\b", re.I)
PROBLEMS_RE = re.compile(r"\b(\d{1,3})\s*(problems?|questions?|items?)\b", re.I)
SLIDES_RE = re.compile(r"\b(\d{1,3})\s*(slides?|frames?)\b", re.I)
SOURCES_RE = re.compile(r"\b(\d{1,2})\s*(sources?|citations?)\b", re.I)
CHAPTERS_RE = re.compile(r"\b(chapter|section)\s*(\d{1,3})\b", re.I)
TIMED_RE = re.compile(r"\b(\d{1,3})\s*(min|minutes|mins|h|hours)\b.*\b(quiz|test|exam|presentation|talk)\b", re.I)
VIDEO_RE = re.compile(r"\b(\d{1,3})\s*(min|minutes|mins|h|hours)\b.*\b(video|recording|presentation)\b", re.I)
DRAFT_RE = re.compile(r"\b(draft|outline)\b", re.I)
FINAL_RE = re.compile(r"\b(final|finalized|camera[- ]ready)\b", re.I)
GROUP_RE = re.compile(r"\b(group|team|pair|collaborative)\b", re.I)
OPEN_BOOK_RE = re.compile(r"\b(open[- ]book)\b", re.I)
MCQ_RE = re.compile(r"\b(multiple[- ]choice|mcq)\b", re.I)
DEBUG_KEYWORDS_RE = re.compile(r"\b(debug|bug|issue|fix)\b", re.I)

def classify_task(title: str, desc: str = "", link: str | None = None) -> str:
    text = f"{title}\n{desc}\n{link or ''}".lower()
    for t, pat in TYPE_PATTERNS:
        if re.search(pat, text, re.I):
            return t
    # fallback: quick guesses
    if "submit" in text and "quiz" in text: return "quiz"
    if "submit" in text and "essay" in text: return "essay"
    return "unknown"

def parse_quantifiers(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if m := WORDS_RE.search(text):  out["words"] = int(m.group(1))
    if m := PAGES_RE.search(text):  out["pages"] = int(m.group(1))
    if m := PROBLEMS_RE.search(text): out["problems"] = int(m.group(1))
    if m := SLIDES_RE.search(text): out["slides"] = int(m.group(1))
    if m := SOURCES_RE.search(text): out["sources"] = int(m.group(1))
    if m := CHAPTERS_RE.search(text): out.setdefault("chapters", []).append(int(m.group(2)))
    if m := TIMED_RE.search(text):
        n, unit = int(m.group(1)), m.group(2).lower()
        out["timed_minutes"] = n if unit.startswith("m") else n*60
        out["is_timed_assessment"] = True
    if m := VIDEO_RE.search(text):
        n, unit = int(m.group(1)), m.group(2).lower()
        out["video_minutes"] = n if unit.startswith("m") else n*60
    out["is_draft"] = bool(DRAFT_RE.search(text))
    out["is_final"] = bool(FINAL_RE.search(text))
    out["is_group"] = bool(GROUP_RE.search(text))
    out["open_book"] = bool(OPEN_BOOK_RE.search(text))
    out["mcq"] = bool(MCQ_RE.search(text))
    out["mentions_debugging"] = bool(DEBUG_KEYWORDS_RE.search(text))
    return out

def estimate_minutes(task_type: str, title: str, desc: str) -> Tuple[int, Dict[str, Any]]:
    text = f"{title}\n{desc}".lower()
    base = BASELINE_MIN.get(task_type, BASELINE_MIN["unknown"])
    q = parse_quantifiers(text)

    est = base

    # 3) Modifiers by signals
    if task_type in ("essay","report","proposal"):
        if "words" in q:  # ~3 min per 50 words drafting+edit (coarse)
            est = max(est, int(q["words"] * 3/50 * 50))  # snap to 50m blocks
        if "pages" in q:  # ~25 min per page baseline
            est = max(est, q["pages"] * 25)
        if "sources" in q: est = max(est, est + q["sources"] * 20)
        if q.get("is_draft"): est = int(est * 0.6)
        if q.get("is_final"): est = int(est * 1.25)
    if task_type in ("problem_set","worksheet","exercise"):
        if "pages" in q: est += q["pages"] * 10
        if "words" in q: est += int(q["words"] / 200) * 10
        if "problems" in q: est = max(est, q["problems"] * 12)
    if task_type in ("quiz","exam"):
        if q.get("is_timed_assessment"):
            est = max(est, int(q["timed_minutes"] * 0.5))  # study time ~ 0.5x test duration
        if q.get("mcq"): est = int(est * 0.8)
        if q.get("open_book"): est = int(est * 0.85)
    if task_type == "reading":
        if "pages" in q: est = max(est, q["pages"] * 4)  # ~4 min/page college dense
        if "words" in q: est = max(est, int(q["words"]/250))  # 250 wpm
        if "chapters" in q: est = max(est, len(q["chapters"]) * 35)
    if task_type in ("presentation","project","lab"):
        if q.get("is_group"): est = int(est * 0.85)  # distributed work
        if q.get("is_final"): est = int(est * 1.2)
        if "slides" in q: est = max(est, q["slides"] * 8)
        if "video_minutes" in q:
            # Rough editing time ~3x runtime
            est = max(est, q["video_minutes"] * 3)
    if task_type == "coding":
        if q.get("mentions_debugging"): est = int(est * 1.2)
        if "problems" in q: est = max(est, q["problems"] * 25)
        if q.get("is_group"): est = int(est * 0.9)
    if task_type == "data_analysis":
        if "problems" in q: est = max(est, q["problems"] * 20)
        if "pages" in q: est = max(est, q["pages"] * 15)
    if task_type == "design_doc":
        if "pages" in q: est = max(est, q["pages"] * 20)
        if q.get("is_final"): est = int(est * 1.15)
    if task_type == "discussion":
        if "words" in q: est = max(est, int(q["words"] / 150) * 15 + 20)
        if q.get("is_final"): est = int(est * 1.1)
    if task_type == "proposal":
        if "words" in q: est = max(est, int(q["words"] * 3/60) * 60)
        if "sources" in q: est += q["sources"] * 15

    # clamp & round
    est = max(20, min(est, 8*60))  # 20m .. 8h
    # round to 10 min
    est = int(round(est / 10) * 10)
    return est, {"task_type": task_type, **q}

def suggested_start(due_at: datetime, minutes: int) -> datetime:
    # Long tasks need earlier runway. Buffer = max(2h, 1.5x estimate) capped.
    buffer = timedelta(minutes=min(max(120, int(minutes*1.5)), 60*24*7))  # cap 7d
    anchor = due_at if due_at.tzinfo else due_at.replace(tzinfo=DEFAULT_TIMEZONE)
    return (anchor - buffer).astimezone(DEFAULT_TIMEZONE)

def analyze_assignment(title: str, desc: str, due_at: datetime, link: str | None = None) -> Dict[str, Any]:
    ttype = classify_task(title, desc, link)
    minutes, signals = estimate_minutes(ttype, title, desc)
    start = suggested_start(due_at, minutes)
    return {
        "task_type": ttype,
        "estimated_minutes": minutes,
        "suggested_start_utc": start.isoformat(),
        "signals": signals
    }
