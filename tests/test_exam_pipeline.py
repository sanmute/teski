"""Tests for app/exam_scraper/scraper.py and app/exam_pipeline/agent.py."""

from __future__ import annotations

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Stub packages that may not be installed in the test environment.
# These are transitively imported by app.feedback.clients but are not
# exercised by the pipeline logic under test — we patch _get_anthropic
# directly in the tests that need it.
for _pkg in ("tiktoken", "anthropic", "openai", "faster_whisper", "pydub"):
    sys.modules.setdefault(_pkg, MagicMock())
# Ensure the AsyncAnthropic symbol resolves inside the stub.
sys.modules["anthropic"].AsyncAnthropic = MagicMock

from app.exam_scraper.scraper import parse_exam_table, search_courses
from app.exam_pipeline.agent import generate_from_pdfs
from app.exam_pipeline.router import router as exam_pipeline_router


# ── HTML fixtures ─────────────────────────────────────────────────────────────

_HTML_TWO_ROWS = """\
<table>
  <tr>
    <th>Code</th><th>Name</th><th>Department</th><th>Date</th><th>Download</th>
  </tr>
  <tr>
    <td>BH30A1801</td>
    <td>Nuclear Reactor Physics</td>
    <td>Energiatekniikka</td>
    <td>2024-05-15</td>
    <td><a href="https://exams.ltky.fi/wp-content/uploads/nuclear.pdf">Download</a></td>
  </tr>
  <tr>
    <td>CS50A0000</td>
    <td>Intro to Computer Science</td>
    <td>Computing</td>
    <td>2023-12-01</td>
    <td><a href="https://exams.ltky.fi/wp-content/uploads/cs50.pdf">Download</a></td>
  </tr>
</table>
"""

_HTML_NO_PDF = """\
<table>
  <tr>
    <th>Code</th><th>Name</th><th>Department</th><th>Date</th><th>Download</th>
  </tr>
  <tr>
    <td>XX00A0000</td>
    <td>No PDF Course</td>
    <td>SomeDept</td>
    <td>2024-01-01</td>
    <td>Not available</td>
  </tr>
</table>
"""


# ── Scraper helpers ───────────────────────────────────────────────────────────

def _row(code: str, name: str, date: str = "2024-01-01") -> dict:
    return {
        "course_code": code,
        "course_name": name,
        "department": "TestDept",
        "date": date,
        "pdf_url": f"https://example.com/{code}.pdf",
    }


# ── Test 1 ────────────────────────────────────────────────────────────────────

def test_parse_exam_table_extracts_rows():
    rows = parse_exam_table(_HTML_TWO_ROWS)

    assert len(rows) == 2

    first = rows[0]
    assert first["course_code"] == "BH30A1801"
    assert first["course_name"] == "Nuclear Reactor Physics"
    assert first["department"] == "Energiatekniikka"
    assert first["date"] == "2024-05-15"
    assert first["pdf_url"].endswith(".pdf")

    assert rows[1]["course_code"] == "CS50A0000"


# ── Test 2 ────────────────────────────────────────────────────────────────────

def test_parse_exam_table_skips_missing_pdf():
    rows = parse_exam_table(_HTML_NO_PDF)
    assert rows == []


# ── Test 3 ────────────────────────────────────────────────────────────────────

def test_search_courses_case_insensitive():
    rows = [
        _row("STAT101", "Statistics I"),
        _row("STAT102", "STATISTICS II"),
        _row("MATH101", "Calculus"),
    ]
    results = search_courses(rows, "statistics")

    assert len(results) == 2
    codes = {r["course_code"] for r in results}
    assert codes == {"STAT101", "STAT102"}


# ── Test 4 ────────────────────────────────────────────────────────────────────

def test_search_courses_returns_max_10():
    rows = [_row(f"STAT{i:03d}", f"Statistics {i}") for i in range(15)]
    results = search_courses(rows, "statistics")
    assert len(results) == 10


# ── Test 5 ────────────────────────────────────────────────────────────────────

def test_search_courses_sorted_by_date():
    rows = [
        _row("A", "Algebra", date="2022-09-01"),
        _row("B", "Algebra Advanced", date="2024-03-15"),
        _row("C", "Algebra Basics", date="2023-05-10"),
    ]
    results = search_courses(rows, "algebra")

    dates = [r["date"] for r in results]
    assert dates == sorted(dates, reverse=True)


# ── Agent mock helper ─────────────────────────────────────────────────────────

def _mock_anthropic_client(json_payload: list[dict]) -> MagicMock:
    """Return a mock Anthropic client whose messages.create returns json_payload."""
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = json.dumps(json_payload)

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    return mock_client


_VALID_EXERCISE: dict = {
    "id": "calc-001",
    "concept": "Integration by power rule",
    "type": "mcq",
    "question": "What is the integral of 2x dx?",
    "difficulty": 2,
    "skill_ids": ["calculus"],
    "keywords": ["integral", "power-rule"],
    "course": "Calculus I",
    "domain": "Mathematics",
    "meta": {
        "choices": [
            {"text": "x^2 + C", "correct": True},
            {"text": "2x^2 + C", "correct": False},
            {"text": "x + C", "correct": False},
        ]
    },
    "explanation": "By the power rule, the integral of 2x is x^2 + C.",
}


# ── Test 6 ────────────────────────────────────────────────────────────────────

def test_generate_from_pdfs_parses_json_response():
    payload = [
        _VALID_EXERCISE,
        {**_VALID_EXERCISE, "id": "calc-002"},
        {**_VALID_EXERCISE, "id": "calc-003"},
    ]
    mock_client = _mock_anthropic_client(payload)

    with patch("app.exam_pipeline.agent._get_anthropic", return_value=mock_client):
        results = asyncio.run(
            generate_from_pdfs(
                pdf_bytes_list=[b"%PDF-1.4 fake"],
                course_name="Calculus I",
                num_exercises=3,
            )
        )

    assert len(results) == 3
    assert all("raw_markdown" in r for r in results)
    assert results[0]["id"] == "calc-001"
    # raw_markdown should be non-empty YAML front matter + body
    assert results[0]["raw_markdown"].startswith("---")


# ── Test 7 ────────────────────────────────────────────────────────────────────

def test_generate_from_pdfs_skips_invalid_exercise():
    # Remove the required "question" field to make the second exercise invalid.
    invalid = {k: v for k, v in _VALID_EXERCISE.items() if k != "question"}
    payload = [_VALID_EXERCISE, {**invalid, "id": "calc-bad"}]
    mock_client = _mock_anthropic_client(payload)

    with patch("app.exam_pipeline.agent._get_anthropic", return_value=mock_client):
        results = asyncio.run(
            generate_from_pdfs(
                pdf_bytes_list=[b"%PDF-1.4 fake"],
                course_name="Calculus I",
                num_exercises=2,
            )
        )

    assert len(results) == 1
    assert results[0]["id"] == "calc-001"


# ── Test 8 ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def save_client():
    test_app = FastAPI()
    test_app.include_router(exam_pipeline_router)
    return TestClient(test_app)


def test_save_endpoint_writes_files(tmp_path, save_client):
    raw_markdown = "---\nid: calc-001\ntype: mcq\n---\n\n## Answer\nx^2 + C\n"
    exercise = {**_VALID_EXERCISE, "raw_markdown": raw_markdown}

    resp = save_client.post(
        "/exam-pipeline/save",
        json={"exercises": [exercise], "content_dir": str(tmp_path)},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["saved"]) == 1
    assert data["skipped"] == []

    written = tmp_path / "calc-001.md"
    assert written.exists()
    assert written.read_text(encoding="utf-8") == raw_markdown
