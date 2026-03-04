from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.exam_pipeline.agent import generate_from_pdfs
from app.exam_pipeline.schemas import (
    GeneratedExerciseOut,
    PipelineRequest,
    PipelineResponse,
)
from app.exam_scraper.schemas import CourseSearchResponse, ExamResult
from app.exam_scraper.scraper import (
    download_pdf,
    get_cached_index,
    search_courses,
)
from app.exercises import invalidate_cache

router = APIRouter(prefix="/exam-pipeline", tags=["exam-pipeline"])


# ---------------------------------------------------------------------------
# Endpoint 1 — course search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=CourseSearchResponse)
async def search_exams(q: str = Query(..., min_length=1)):
    """Search the LTKY exam archive by course name or code.

    No authentication required — public discovery endpoint.
    """
    rows = await get_cached_index()
    matches = search_courses(rows, q)
    return CourseSearchResponse(
        query=q,
        results=[ExamResult(**row) for row in matches],
        total_found=len(matches),
    )


# ---------------------------------------------------------------------------
# Endpoint 2 — generate exercises from exam PDFs
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=PipelineResponse)
async def generate_exercises(request: PipelineRequest):
    """Download exam PDFs and generate practice exercises via Claude.

    TODO: restrict to authenticated users before production.
    """
    # Download all PDFs concurrently (capped at 3 by PipelineRequest validator).
    try:
        pdf_bytes_list: list[bytes] = list(
            await asyncio.gather(*[download_pdf(url) for url in request.pdf_urls])
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"PDF download failed: {exc}") from exc

    raw_exercises = await generate_from_pdfs(
        pdf_bytes_list=pdf_bytes_list,
        course_name=request.course_name,
        num_exercises=request.num_exercises,
        exercise_types=request.exercise_types,
        difficulty_range=(request.difficulty_min, request.difficulty_max),
    )

    exercises = [GeneratedExerciseOut(**ex) for ex in raw_exercises]
    return PipelineResponse(
        course_name=request.course_name,
        exercises=exercises,
        pdf_count=len(pdf_bytes_list),
        source_urls=request.pdf_urls,
    )


# ---------------------------------------------------------------------------
# Endpoint 3 — save exercises to content/
# ---------------------------------------------------------------------------


class _SaveRequest(BaseModel):
    exercises: list[GeneratedExerciseOut]
    content_dir: str = "content"


class _SaveResponse(BaseModel):
    saved: list[str]
    skipped: list[str]


@router.post("/save", response_model=_SaveResponse)
def save_exercises(request: _SaveRequest):
    """Write generated exercises to the content/ directory as Markdown files.

    Skips any exercise whose target file already exists (no overwrites).

    TODO: restrict to admin users before production.
    """
    content_dir = Path(request.content_dir)
    content_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    skipped: list[str] = []

    for exercise in request.exercises:
        target = content_dir / f"{exercise.id}.md"
        if target.exists():
            skipped.append(exercise.id)
            continue
        target.write_text(exercise.raw_markdown, encoding="utf-8")
        saved.append(str(target))

    if saved:
        invalidate_cache()

    return _SaveResponse(saved=saved, skipped=skipped)


# ---------------------------------------------------------------------------
# Endpoint 4 — health check
# ---------------------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, Any]:
    """Liveness probe for the exam pipeline."""
    return {"status": "ok", "source": "https://exams.ltky.fi"}
