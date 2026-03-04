"""Scraper for the LTKY open exam archive (https://exams.ltky.fi/).

The archive is an open, public WordPress site that renders exam records in an
HTML table inside a ``div.facetwp-template`` container.  There is no public
REST API — we fetch the static HTML and parse it with ``html.parser``.

Column order in the table (positional, no class names):
    0  course_code  — e.g. "BH30A1801"
    1  course_name  — e.g. "Nuclear Reactor Physics Analyses"
    2  department   — e.g. "Energiatekniikka"
    3  date         — ISO 8601 "YYYY-MM-DD" string
    4  download     — <a href="…wp-content/uploads/…/file.pdf">Download</a>

Limitations
-----------
The initial page load may only contain a subset of all archived exams because
FacetWP paginates results.  For full-archive access a future enhancement could
POST to ``/wp-json/facetwp/v1/refresh`` with a high per_page value; that is
out of scope here.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx
from fastapi import HTTPException

_INDEX_URL = "https://exams.ltky.fi/"
_FETCH_TIMEOUT = 20   # seconds
_DOWNLOAD_TIMEOUT = 30  # seconds

# Minimum columns a row must have to be treated as a data row.
_MIN_DATA_COLS = 5

# Column positions (zero-indexed) — matches the observed table layout.
_COL_CODE = 0
_COL_NAME = 1
_COL_DEPT = 2
_COL_DATE = 3
_COL_PDF = 4

# Header keyword hints used to confirm or remap column order if a header row
# is present.  Each entry is (keyword_substring, canonical_field).
_HEADER_HINTS: list[tuple[str, str]] = [
    ("code",       "course_code"),
    ("kurssikoodi","course_code"),
    ("name",       "course_name"),
    ("nimi",       "course_name"),
    ("department", "department"),
    ("laitos",     "department"),
    ("osasto",     "department"),
    ("date",       "date"),
    ("päivämäärä", "date"),
    ("pvm",        "date"),
    ("download",   "pdf_url"),
    ("lataa",      "pdf_url"),
    ("pdf",        "pdf_url"),
]

# Date pattern regexes for normalisation.
_RE_YYYYMMDD = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_RE_DDMMYYYY = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")
_RE_DDMMYY   = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2})")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_exam_index() -> str:
    """GET the exam archive index page and return its raw HTML.

    Returns
    -------
    str
        Raw HTML of https://exams.ltky.fi/.

    Raises
    ------
    HTTPException(502)
        On any network failure — timeout, DNS error, or non-2xx HTTP status.
    """
    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT, follow_redirects=True
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

    Parameters
    ----------
    html:
        Raw HTML returned by :func:`fetch_exam_index`.

    Returns
    -------
    list[dict]
        One dict per valid exam row.
    """
    parser = _ExamTableParser()
    parser.feed(html)
    return parser.rows


def search_courses(rows: list[dict], query: str) -> list[dict]:
    """Case-insensitive substring search across course_code and course_name.

    A row matches if ``query`` appears anywhere in either field.  Returns the
    top 10 matches sorted by date descending (most-recent first).  Rows with
    an empty date string sort after all dated rows.

    Parameters
    ----------
    rows:
        Output from :func:`parse_exam_table`.
    query:
        Search string; must be a non-empty substring.

    Returns
    -------
    list[dict]
        Up to 10 matching rows, newest first.
    """
    q = query.lower()
    matches = [
        row for row in rows
        if q in row.get("course_code", "").lower()
        or q in row.get("course_name", "").lower()
    ]
    # Empty date strings sort before "0000-…" when reversed, so we treat them
    # as the empty string directly — they naturally sink to the bottom.
    matches.sort(key=lambda r: r.get("date") or "", reverse=True)
    return matches[:10]


async def download_pdf(pdf_url: str) -> bytes:
    """Download a PDF from the exam archive and return its raw bytes.

    Parameters
    ----------
    pdf_url:
        Absolute URL to a ``.pdf`` file, typically taken from an
        :class:`~app.exam_scraper.schemas.ExamResult` ``pdf_url`` field.

    Returns
    -------
    bytes
        Raw PDF content.

    Raises
    ------
    HTTPException(502)
        On any network failure — timeout, connection error, or non-2xx status.
    """
    try:
        async with httpx.AsyncClient(
            timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True
        ) as client:
            response = await client.get(pdf_url)
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

    The PDF URL is taken from the ``href`` attribute of any ``<a>`` tag
    inside the download cell; if the download column is not identified, any
    ``.pdf`` href in the row is used as a fallback.
    """

    def __init__(self) -> None:
        super().__init__()

        # ---- table-depth tracking ----
        self._table_depth: int = 0

        # ---- facetwp-template div tracking ----
        self._in_template_div: bool = False
        self._template_div_depth: int = 0  # nesting depth of divs inside it

        # ---- active row tracking ----
        # True when we're in a <tr> that we should process (depth==1 or template div).
        self._in_row: bool = False
        self._row_has_th: bool = False
        self._row_start_depth: int = 0  # table depth when row started

        # ---- active cell tracking ----
        self._in_cell: bool = False
        self._cell_is_th: bool = False
        self._cell_depth: int = 0      # table depth when cell started
        self._cell_href: str | None = None
        self._cell_text: list[str] = []

        # ---- accumulated row cells ----
        self._row_cells: list[tuple[str, str | None]] = []  # (text, href|None)

        # ---- column index map (field_name -> column index) ----
        # Populated from the header row; falls back to _COL_* constants.
        self._col_index: dict[str, int] | None = None

        # ---- output ----
        self.rows: list[dict] = []

    # ------------------------------------------------------------------
    # HTMLParser callbacks
    # ------------------------------------------------------------------

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        a = dict(attrs)

        # ---- div tracking for facetwp-template ----
        if tag == "div":
            classes = (a.get("class") or "").split()
            if "facetwp-template" in classes:
                self._in_template_div = True
                self._template_div_depth = 0
                return
            if self._in_template_div:
                self._template_div_depth += 1
            return

        # ---- table depth ----
        if tag == "table":
            self._table_depth += 1
            return

        # ---- row start ----
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

        # ---- cell start ----
        if tag in ("th", "td") and self._in_row:
            # Only open cells at the same table depth the row started at,
            # to avoid processing cells of nested tables.
            if self._table_depth == self._row_start_depth:
                self._in_cell = True
                self._cell_is_th = tag == "th"
                self._cell_depth = self._table_depth
                self._cell_href = None
                self._cell_text = []
                if self._cell_is_th:
                    self._row_has_th = True
            return

        # ---- anchor inside cell ----
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
            # Only close if at the same depth the cell was opened.
            if self._table_depth == self._cell_depth:
                self._in_cell = False
                text = " ".join(self._cell_text).strip()
                self._row_cells.append((text, self._cell_href))
            return

        if tag == "tr" and self._in_row:
            # Only finalise the row if we're back at the depth it started.
            if self._table_depth == self._row_start_depth:
                self._in_row = False
                self._process_row()

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            stripped = data.strip()
            if stripped:
                self._cell_text.append(stripped)

    # ------------------------------------------------------------------
    # Row processing
    # ------------------------------------------------------------------

    def _process_row(self) -> None:
        cells = self._row_cells
        if not cells:
            return

        # ---- detect and store header row ----
        is_header = self._row_has_th
        if not is_header and self._col_index is None:
            # Check if cell texts look like column headers.
            texts_lower = [c[0].lower() for c in cells]
            for key, _ in _HEADER_HINTS:
                if any(key in t for t in texts_lower):
                    is_header = True
                    break

        if is_header:
            if self._col_index is None:
                self._col_index = self._parse_header_cells(cells)
            return  # don't emit header as a data row

        # ---- emit data row ----
        if len(cells) < _MIN_DATA_COLS:
            return

        col = self._col_index or {}

        def text_at(field: str, default_pos: int) -> str:
            idx = col.get(field, default_pos)
            return cells[idx][0] if idx < len(cells) else ""

        def href_at(field: str, default_pos: int) -> str | None:
            idx = col.get(field, default_pos)
            return cells[idx][1] if idx < len(cells) else None

        # PDF URL: prefer the href from the designated download column; fall
        # back to any .pdf href anywhere in the row.
        pdf_url = href_at("pdf_url", _COL_PDF) or ""
        if not pdf_url:
            for _, href in cells:
                if href and href.lower().endswith(".pdf"):
                    pdf_url = href
                    break

        if not pdf_url or not pdf_url.lower().endswith(".pdf"):
            return  # skip rows without a PDF download

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
        """Return a field → column-index map derived from header cell texts."""
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

    Recognised patterns
    -------------------
    - ``YYYY-MM-DD`` — returned unchanged.
    - ``DD.MM.YYYY`` or ``DD-MM-YYYY`` or ``DD/MM/YYYY`` — Finnish / European.
    - ``DD.MM.YY`` — two-digit year; 00–69 → 2000s, 70–99 → 1900s.

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
