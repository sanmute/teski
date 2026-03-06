"""LUT Sisu course catalog fetcher.

The Kori search API requires a ``fullTextQuery`` to return results — it will
not dump the full catalog without one.  We work around this by running several
single-letter queries ('a', 'e', 'i', 'o', 'u', 'r') and deduplicating by
course code.  Empirically this covers ~96 % of the ~1 924 active LUT courses.

The API has a hard cap of 1 000 results per query (``start >= 1000`` always
returns empty), so we stop when a page comes back empty.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://sisu.lut.fi/kori/api/course-unit-search"
_ORG_ID = "lut-university-root-id"
_LIMIT = 1000
# Single-letter queries that together cover ~96 % of LUT courses (a=856, e=953,
# i=778, o=752, u=114, r=243 unique results, ~1847 total after dedup).
_QUERIES = ["a", "e", "i", "o", "u", "r"]
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Teski/1.0; educational research)"}

SISU_CACHE_TTL: int = 86400  # 24 hours — course catalog changes slowly
_sisu_cache: list[dict] | None = None
_sisu_cache_at: float = 0.0


async def fetch_sisu_course_index() -> list[dict]:
    """Fetch LUT courses from the Sisu Kori search API.

    Makes one request per query letter, deduplicates by course code, and
    normalises each result to::

        {"code": str, "name_fi": str, "name_en": str, "credits": float}

    Returns
    -------
    list[dict]
        All unique LUT courses discovered across the query set.
    """
    seen_codes: set[str] = set()
    results: list[dict] = []

    async with httpx.AsyncClient(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
        # Fetch English names in a first pass.
        for q in _QUERIES:
            new_from_query = await _fetch_query(client, q, uiLang="en")
            for item in new_from_query:
                code = item["code"]
                if code not in seen_codes:
                    seen_codes.add(code)
                    results.append(item)

        # Second pass with uiLang=fi to fill in Finnish names for courses we
        # already discovered (update in-place via a lookup dict).
        by_code: dict[str, dict] = {r["code"]: r for r in results}
        for q in _QUERIES:
            fi_items = await _fetch_query(client, q, uiLang="fi")
            for item in fi_items:
                code = item["code"]
                if code in by_code:
                    by_code[code]["name_fi"] = item["name_en"]  # name_en holds the raw name

    logger.info("Sisu catalog: fetched %d unique LUT courses", len(results))
    return results


async def _fetch_query(client: httpx.AsyncClient, q: str, uiLang: str) -> list[dict]:
    """Fetch all pages for a single fullTextQuery letter."""
    items: list[dict] = []
    start = 0
    while True:
        try:
            resp = await client.get(
                _BASE_URL,
                params={
                    "universityOrgId": _ORG_ID,
                    "fullTextQuery": q,
                    "limit": _LIMIT,
                    "start": start,
                    "uiLang": uiLang,
                },
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Sisu fetch error (q=%r, start=%d): %s", q, start, exc)
            break

        data = resp.json()
        page: list[dict[str, Any]] = data.get("searchResults") or []
        if not page:
            break  # empty page or API hard-cap reached

        for raw in page:
            code = (raw.get("code") or "").strip()
            if not code:
                continue
            name = (raw.get("name") or "").strip()
            credits_raw = raw.get("credits") or {}
            credits_val = credits_raw.get("min") or credits_raw.get("max") or 0
            items.append({
                "code": code,
                "name_en": name,   # placeholder; name_fi filled by caller
                "name_fi": name,
                "credits": float(credits_val),
            })

        if len(page) < _LIMIT or data.get("truncated"):
            break  # last page or API cap
        start += _LIMIT

    return items


async def get_sisu_index() -> list[dict]:
    """Return the cached Sisu course list, refreshing after SISU_CACHE_TTL seconds."""
    global _sisu_cache, _sisu_cache_at
    if _sisu_cache is not None and (time.time() - _sisu_cache_at) < SISU_CACHE_TTL:
        return _sisu_cache
    _sisu_cache = await fetch_sisu_course_index()
    _sisu_cache_at = time.time()
    return _sisu_cache
