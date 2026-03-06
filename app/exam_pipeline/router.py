from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.exam_pipeline.agent import generate_from_pdfs
from app.exam_pipeline.schemas import (
    GeneratedExerciseOut,
    PipelineRequest,
    PipelineResponse,
)
from app.exam_scraper.schemas import CourseSearchResponse, ExamResult
from app.exam_scraper.course_index import get_sisu_index
from app.exam_scraper.scraper import (
    download_pdf,
    get_cached_index,
    search_courses,
)
from app.exercises import invalidate_cache

# DB integration — present in the deployed backend; silently skipped for local/test env.
try:
    from db import get_session as _get_db_session          # type: ignore[import]
    from models_exercise import Exercise as _DbExercise    # type: ignore[import]
    _HAS_DB = True
except ImportError:
    _HAS_DB = False

    def _get_db_session():  # type: ignore[misc]
        yield None

router = APIRouter(prefix="/exam-pipeline", tags=["exam-pipeline"])


# ---------------------------------------------------------------------------
# Endpoint 1 — course search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=CourseSearchResponse)
async def search_exams(q: str = Query(..., min_length=1)):
    """Search LUT courses (Sisu catalog + LTKY exam archive).

    Phase 1 searches the full Sisu course index (~1 900 courses, 24-h cache).
    Phase 2 supplements with any exam-archive courses not in the Sisu cache.
    Results are annotated with has_exams / exam_count / exam_pdf_urls.

    No authentication required — public discovery endpoint.
    """
    exam_rows_coro = get_cached_index()
    try:
        exam_rows, sisu_rows = await asyncio.gather(
            exam_rows_coro,
            get_sisu_index(),
        )
    except Exception:
        # get_sisu_index() failed — run exam_rows_coro alone and fall back.
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "Sisu index unavailable; falling back to exam-archive-only search",
            exc_info=True,
        )
        exam_rows = await get_cached_index()
        sisu_rows = []
    matches = search_courses(exam_rows, q, sisu_rows=sisu_rows)
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
def save_exercises(request: _SaveRequest, db=Depends(_get_db_session)):
    """Write generated exercises to the content/ directory and the database.

    Skips any exercise whose target file already exists (no overwrites).

    TODO: restrict to admin users before production.
    """
    content_dir = Path(request.content_dir)
    content_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    skipped: list[str] = []
    saved_exercises: list[GeneratedExerciseOut] = []

    for exercise in request.exercises:
        target = content_dir / f"{exercise.id}.md"
        if target.exists():
            skipped.append(exercise.id)
            continue
        target.write_text(exercise.raw_markdown, encoding="utf-8")
        saved.append(str(target))
        saved_exercises.append(exercise)

    if saved:
        invalidate_cache()
        if db is not None:
            _upsert_to_db(db, saved_exercises)

    return _SaveResponse(saved=saved, skipped=skipped)


def _upsert_to_db(session: Any, exercises: list[GeneratedExerciseOut]) -> None:
    """Upsert exercises into the SQLite database read by the /ex/list endpoint."""
    for ex in exercises:
        meta = ex.meta or {}

        if ex.type == "mcq":
            choices_raw = meta.get("choices") or []
            choices = [str(c.get("text", "")) for c in choices_raw if isinstance(c, dict)]
            correct = next(
                (str(c.get("text", "")) for c in choices_raw if isinstance(c, dict) and c.get("correct")),
                "",
            )
        elif ex.type == "numeric":
            choices = None
            answer = meta.get("answer") or {}
            correct = str(answer.get("value", ""))
        else:  # short_answer
            choices = None
            rubric = meta.get("rubric") or {}
            must_include = rubric.get("must_include") or []
            correct = "; ".join(str(k) for k in must_include) if must_include else ""

        db_meta = {
            "concept": ex.concept,
            "keywords": ex.keywords,
            "course": ex.course,
            "domain": ex.domain,
            **meta,
        }

        existing = session.get(_DbExercise, ex.id)
        payload = dict(
            id=ex.id,
            question_text=ex.question,
            type=ex.type,
            choices=choices,
            correct_answer=correct,
            difficulty=ex.difficulty,
            skill_ids=ex.skill_ids or [],
            solution_explanation=ex.explanation or None,
            hint=None,
            meta=db_meta,
            updated_at=datetime.utcnow(),
        )
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            session.add(_DbExercise(**payload))
    session.commit()


# ---------------------------------------------------------------------------
# Endpoint 4 — health check
# ---------------------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, Any]:
    """Liveness probe for the exam pipeline."""
    return {"status": "ok", "source": "https://exams.ltky.fi"}
