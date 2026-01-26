# services/topic_matcher.py
from __future__ import annotations
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from services.topic_map import TOPIC_MAP  # your big dict

_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+")

def _norm(s: str) -> str:
    return " ".join(_WORD.findall((s or "").lower()))

def _keyword_hits(text: str, keywords: List[str]) -> int:
    """Counts hits. Single tokens use word-boundary; phrases use substring on normalized text."""
    score = 0
    for kw in keywords:
        kw_norm = _norm(kw)
        if " " in kw_norm:  # phrase
            if kw_norm in text:
                score += 2  # phrases are stronger signals
        else:
            # whole-word match
            if re.search(rf"\b{re.escape(kw_norm)}\b", text):
                score += 1
    return score

def match_topics(title: str, notes: str = "", max_topics: int = 4, min_score: int = 1) -> List[Tuple[str,int]]:
    """
    Returns list of (topic_id, score) sorted by score desc, then by topic_id.
    Can return multiple topics for things like 'history presentation' etc.
    """
    text = _norm(f"{title}\n{notes}")
    scores: Dict[str,int] = {}
    for topic_id, spec in TOPIC_MAP.items():
        kws = spec.get("keywords", [])
        if not kws: 
            continue
        hits = _keyword_hits(text, kws)
        if hits >= min_score:
            scores[topic_id] = hits
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:max_topics]

def merge_resources(topic_ids: List[str], limit: int = 3) -> List[Dict]:
    """
    Merge top resources across topics while deduping by URL and diversifying types.
    Heuristic priority: notes/guides > practice/tools > video/course > data/reference.
    """
    type_rank = {
        "notes": 10, "guide": 10, "method": 10,
        "practice": 9, "exercise": 9, "template": 9,
        "tool": 8,
        "video": 7, "course": 7, "lesson": 7,
        "reference": 6, "source": 6, "data": 6, "library": 6, "gallery": 6
    }
    seen = set()
    pool: List[Tuple[int, Dict]] = []
    for tid in topic_ids:
        spec = TOPIC_MAP.get(tid) or {}
        for r in spec.get("resources", []):
            url = r.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            rank = type_rank.get(r.get("type","").lower(), 5)
            pool.append((rank, r))
    # sort: higher rank first, keep original order tie-break naturally
    pool.sort(key=lambda x: -x[0])
    top = [r for _, r in pool[:limit]]
    return top

def merge_practice_prompts(topic_ids: List[str], limit: int = 2) -> List[Dict]:
    out = []
    for tid in topic_ids:
        for p in TOPIC_MAP.get(tid, {}).get("practice", [])[:limit]:
            out.append({"topic": tid, **p})
    # take first N in round-robin-ish order
    return out[:limit]
