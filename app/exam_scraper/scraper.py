"""Scraper for the LTKY open exam archive (https://exams.ltky.fi/).

The archive is an open, public WordPress site that renders exam records in an
HTML table inside a ``div.facetwp-template`` container.  There is no public
REST API and URL query parameters are ignored server-side — filtering happens
in client-side JavaScript after the full page loads.

Our approach
------------
1. Fetch the full index once (≈25 KB of HTML).
2. Parse the entire ``<table>`` in Python using only stdlib ``html.parser``.
3. Cache the parsed rows in memory for :data:`CACHE_TTL` seconds (30 min) to
   avoid hammering the site.
4. Apply our own substring filter in :func:`search_courses`.

Column order in the table (positional, no class names):
    0  course_code  — e.g. "BH30A1801"
    1  course_name  — e.g. "Nuclear Reactor Physics Analyses"
    2  department   — e.g. "Energiatekniikka"
    3  date         — ISO 8601 "YYYY-MM-DD" string
    4  download     — <a href="…wp-content/uploads/…/file.pdf">Download</a>
"""

from __future__ import annotations

import re
import time
from html.parser import HTMLParser

import httpx
from fastapi import HTTPException

_INDEX_URL = "https://exams.ltky.fi/"
_FETCH_TIMEOUT = 20    # seconds
_DOWNLOAD_TIMEOUT = 30  # seconds
_USER_AGENT = "Mozilla/5.0 (compatible; Teski/1.0; educational research)"

# Minimum columns a row must have to be treated as a data row.
_MIN_DATA_COLS = 5

# Column positions (zero-indexed) — matches the observed table layout.
_COL_CODE = 0
_COL_NAME = 1
_COL_DEPT = 2
_COL_DATE = 3
_COL_PDF = 4

# Header keyword hints used to confirm or remap column order if a header row
# is present.
_HEADER_HINTS: list[tuple[str, str]] = [
    ("code",        "course_code"),
    ("kurssikoodi", "course_code"),
    ("name",        "course_name"),
    ("nimi",        "course_name"),
    ("department",  "department"),
    ("laitos",      "department"),
    ("osasto",      "department"),
    ("date",        "date"),
    ("päivämäärä",  "date"),
    ("pvm",         "date"),
    ("download",    "pdf_url"),
    ("lataa",       "pdf_url"),
    ("pdf",         "pdf_url"),
]

# Date pattern regexes for normalisation.
_RE_YYYYMMDD = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_RE_DDMMYYYY = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")
_RE_DDMMYY   = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2})")

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

CACHE_TTL: int = 1800  # 30 minutes

_cache: list[dict] | None = None
_cache_at: float = 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_exam_index() -> str:
    """GET the exam archive index page and return its raw HTML.

    Sets a realistic ``User-Agent`` header so the request is not blocked by
    bot-detection rules on the WordPress host.

    Raises
    ------
    HTTPException(502)
        On any network failure — timeout, DNS error, or non-2xx HTTP status.
    """
    headers = {"User-Agent": _USER_AGENT}
    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            response = await client.get(_INDEX_URL)
            response.raise_for_status()
            return response.text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch exam index: {exc}",
        ) from exc


def parse_exam_table(html: str) -> list[dict]:
    """Parse the exam archive HTML and return a list of exam row dicts.

    Each dict contains the keys ``course_code``, ``course_name``,
    ``department``, ``date`` (YYYY-MM-DD or empty string), and ``pdf_url``
    (absolute URL ending in ``.pdf``).

    Rows that have no ``.pdf`` download link are silently skipped.
    """
    parser = _ExamTableParser()
    parser.feed(html)
    return parser.rows


async def get_cached_index() -> list[dict]:
    """Return the parsed exam table, fetching and caching it if stale.

    The cache is module-level and lives for :data:`CACHE_TTL` seconds.
    Use this function instead of calling :func:`fetch_exam_index` directly
    from route handlers.
    """
    global _cache, _cache_at
    if _cache is not None and (time.time() - _cache_at) < CACHE_TTL:
        return _cache
    html = await fetch_exam_index()
    _cache = parse_exam_table(html)
    _cache_at = time.time()
    return _cache


def search_courses(rows: list[dict], query: str) -> list[dict]:
    """Case-insensitive substring search across course_code and course_name.

    A row matches if ``query`` appears anywhere in either field.  Returns the
    top 10 matches sorted by date descending (most-recent first).  Rows with
    an empty date string sort after all dated rows.

    Parameters
    ----------
    rows:
        Output from :func:`parse_exam_table` or :func:`get_cached_index`.
    query:
        Search string; leading/trailing whitespace is stripped.
    """
    q = query.strip().lower()
    matches = [
        row for row in rows
        if q in row.get("course_code", "").lower()
        or q in row.get("course_name", "").lower()
    ]
    matches.sort(key=lambda r: r.get("date") or "", reverse=True)
    return matches[:10]


async def download_pdf(pdf_url: str) -> bytes:
    """Download a PDF from the exam archive and return its raw bytes.

    Raises
    ------
    HTTPException(502)
        On any network failure — timeout, connection error, or non-2xx status.
    """
    headers = {"User-Agent": _USER_AGENT}
    try:
        async with httpx.AsyncClient(
            timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            response = await client.get(pdf_url, headers=headers)
            response.raise_for_status()
            return response.content
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download PDF from {pdf_url!r}: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# HTML parser
# ---------------------------------------------------------------------------


class _ExamTableParser(HTMLParser):
    """State-machine parser that extracts exam rows from the archive HTML.

    Strategy
    --------
    The exam records live inside a ``<div class="facetwp-template">``
    container as ``<tr>``/``<td>`` elements (with or without a surrounding
    ``<table>`` tag).  The parser therefore has two activation paths:

    1. **Table path** — tracks ``<table>`` nesting depth; activates on
       ``<tr>`` at depth 1 only to avoid processing rows in nested tables.
    2. **Template-div path** — activates when inside
       ``<div class="facetwp-template">`` in case no ``<table>`` wrapper is
       present.

    Column positions are discovered from the first header row (detected by
    the presence of ``<th>`` elements or by matching cell text against
    :data:`_HEADER_HINTS`).  If no header row is found the default positional
    order is used (code=0, name=1, dept=2, date=3, pdf=4).
    """

    def __init__(self) -> None:
        super().__init__()

        self._table_depth: int = 0
        self._in_template_div: bool = False
        self._template_div_depth: int = 0

        self._in_row: bool = False
        self._row_has_th: bool = False
        self._row_start_depth: int = 0

        self._in_cell: bool = False
        self._cell_is_th: bool = False
        self._cell_depth: int = 0
        self._cell_href: str | None = None
        self._cell_text: list[str] = []

        self._row_cells: list[tuple[str, str | None]] = []
        self._col_index: dict[str, int] | None = None

        self.rows: list[dict] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        a = dict(attrs)

        if tag == "div":
            classes = (a.get("class") or "").split()
            if "facetwp-template" in classes:
                self._in_template_div = True
                self._template_div_depth = 0
                return
            if self._in_template_div:
                self._template_div_depth += 1
            return

        if tag == "table":
            self._table_depth += 1
            return

        if tag == "tr":
            active = (
                self._table_depth == 1
                or (self._in_template_div and self._table_depth == 0)
            )
            if active:
                self._in_row = True
                self._row_has_th = False
                self._row_start_depth = self._table_depth
                self._row_cells = []
            return

        if tag in ("th", "td") and self._in_row:
            if self._table_depth == self._row_start_depth:
                self._in_cell = True
                self._cell_is_th = tag == "th"
                self._cell_depth = self._table_depth
                self._cell_href = None
                self._cell_text = []
                if self._cell_is_th:
                    self._row_has_th = True
            return

        if tag == "a" and self._in_cell and self._table_depth == self._cell_depth:
            href = a.get("href") or ""
            if href:
                self._cell_href = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "div":
            if self._in_template_div:
                if self._template_div_depth > 0:
                    self._template_div_depth -= 1
                else:
                    self._in_template_div = False
            return

        if tag == "table":
            self._table_depth = max(0, self._table_depth - 1)
            return

        if tag in ("th", "td") and self._in_cell:
            if self._table_depth == self._cell_depth:
                self._in_cell = False
                text = " ".join(self._cell_text).strip()
                self._row_cells.append((text, self._cell_href))
            return

        if tag == "tr" and self._in_row:
            if self._table_depth == self._row_start_depth:
                self._in_row = False
                self._process_row()

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            stripped = data.strip()
            if stripped:
                self._cell_text.append(stripped)

    def _process_row(self) -> None:
        cells = self._row_cells
        if not cells:
            return

        is_header = self._row_has_th
        if not is_header and self._col_index is None:
            texts_lower = [c[0].lower() for c in cells]
            for key, _ in _HEADER_HINTS:
                if any(key in t for t in texts_lower):
                    is_header = True
                    break

        if is_header:
            if self._col_index is None:
                self._col_index = self._parse_header_cells(cells)
            return

        if len(cells) < _MIN_DATA_COLS:
            return

        col = self._col_index or {}

        def text_at(field: str, default_pos: int) -> str:
            idx = col.get(field, default_pos)
            return cells[idx][0] if idx < len(cells) else ""

        def href_at(field: str, default_pos: int) -> str | None:
            idx = col.get(field, default_pos)
            return cells[idx][1] if idx < len(cells) else None

        pdf_url = href_at("pdf_url", _COL_PDF) or ""
        if not pdf_url:
            for _, href in cells:
                if href and href.lower().endswith(".pdf"):
                    pdf_url = href
                    break

        if not pdf_url or not pdf_url.lower().endswith(".pdf"):
            return

        self.rows.append({
            "course_code": text_at("course_code", _COL_CODE),
            "course_name": text_at("course_name", _COL_NAME),
            "department":  text_at("department",  _COL_DEPT),
            "date":        _normalise_date(text_at("date", _COL_DATE)),
            "pdf_url":     pdf_url,
        })

    @staticmethod
    def _parse_header_cells(
        cells: list[tuple[str, str | None]]
    ) -> dict[str, int]:
        col_index: dict[str, int] = {}
        for col_idx, (text, _) in enumerate(cells):
            text_lower = text.lower()
            for key, field in _HEADER_HINTS:
                if key in text_lower and field not in col_index:
                    col_index[field] = col_idx
                    break
        return col_index


# ---------------------------------------------------------------------------
# Date normalisation
# ---------------------------------------------------------------------------


def _normalise_date(raw: str) -> str:
    """Return a YYYY-MM-DD string from several common date formats.

    Returns an empty string for unrecognised input.
    """
    raw = raw.strip()
    if not raw:
        return ""

    m = _RE_YYYYMMDD.search(raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = _RE_DDMMYYYY.search(raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    m = _RE_DDMMYY.search(raw)
    if m:
        yy = int(m.group(3))
        yyyy = 2000 + yy if yy < 70 else 1900 + yy
        return f"{yyyy}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    return ""
