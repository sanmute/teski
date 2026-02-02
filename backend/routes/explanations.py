from __future__ import annotations

from typing import Optional, Union, List
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select

from db import get_session
from models_exercise import Exercise
# Try to use the richer generator from the mono-repo app package if available;
# fall back to a minimal block builder when running in the slim Fly image.
try:  # pragma: no cover - optional dependency
    from app.explanations.service import generate_explanation_blocks  # type: ignore
except ImportError:  # pragma: no cover
    def _split_sentences(text: str) -> list[str]:
        import re
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    def generate_explanation_blocks(text: str, style: str, analytical_comfort=None):
        """Deterministic, no-LLM explanation blocks so users see more than an echo."""
        style = (style or "big_picture").lower()
        sentences = _split_sentences(text.strip() or "No input provided.")
        summary = sentences[0] if sentences else text
        rest = " ".join(sentences[1:]) if len(sentences) > 1 else text

        if style == "step_by_step":
            steps = [f"Step {i+1}: {s}" for i, s in enumerate(sentences or [text])]
            content = "\n".join(steps)
            return [ExplanationBlock(style="step_by_step", title="Step-by-step explanation", content=content)]

        if style == "analogy":
            analogy_line = f"Think of it like this: {summary}"
            formal = rest or text
            return [
                ExplanationBlock(style="analogy", title="Analogy", content=analogy_line),
                ExplanationBlock(style="analogy", title="Formal explanation", content=formal),
            ]

        if style == "visual":
            bullets = []
            if summary:
                bullets.append(f"• Main idea: {summary}")
            for s in sentences[1:]:
                bullets.append(f"  • Detail: {s}")
            if not bullets:
                bullets = [f"• {text}"]
            return [ExplanationBlock(style="visual", title="Visual outline", content="\n".join(bullets))]

        if style == "problems":
            example = f"Example: Imagine applying this: {summary}"
            explanation = rest or text
            return [
                ExplanationBlock(style="problems", title="Example", content=example),
                ExplanationBlock(style="problems", title="Explanation", content=explanation),
            ]

        # default big_picture
        paraphrase = f"In simple terms: {summary}" if summary else text
        details = rest if rest != summary else text
        return [
            ExplanationBlock(style="big_picture", title="High-level summary", content=paraphrase),
            ExplanationBlock(style="big_picture", title="Details", content=details),
        ]

# Optional: call OpenAI directly if key is present and app package is unavailable.
try:  # pragma: no cover
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


def generate_explanation_blocks_llm(text: str, style: str) -> Optional[List[ExplanationBlock]]:
    """Generate blocks via OpenAI if configured; return None on failure so we can fall back."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    client = OpenAI(api_key=api_key)
    model = os.getenv("EXPLANATIONS_MODEL", "gpt-4o-mini")
    style_label = style.replace("_", " ")
    prompt = (
        f"You are Teski, a concise study companion.\n"
        f"User question: {text}\n"
        f"Produce a {style_label} explanation in 2-3 short paragraphs. "
        f"Plain text only, no markdown, no LaTeX."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You help students understand concepts quickly."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        content = resp.choices[0].message.content.strip()
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()] or [content]
        blocks = []
        if len(paragraphs) == 1:
            blocks.append(ExplanationBlock(style=style, title="Explanation", content=paragraphs[0]))
        else:
            blocks.append(ExplanationBlock(style=style, title="Summary", content=paragraphs[0]))
            blocks.append(ExplanationBlock(style=style, title="Details", content="\n\n".join(paragraphs[1:])))
        return blocks
    except Exception as exc:
        logger.warning("LLM explanation failed: %s", exc)
        return None

router_api = APIRouter(prefix="/api/explanations", tags=["explanations"])
router_compat = APIRouter(prefix="/explanations", tags=["explanations-compat"])
logger = logging.getLogger("explanations")

# Backward-compatible alias expected by older include_router calls
router = router_api


class ExplanationRequest(SQLModel):
    exercise_id: Optional[str] = None
    user_answer: Optional[Union[str, int]] = None
    # Compat path: some clients send free-form text + mode instead of exercise_id
    text: Optional[str] = None
    mode: Optional[str] = None


class ExplanationBlock(SQLModel):
    style: str
    title: Optional[str] = None
    content: str


class ExplanationResponse(SQLModel):
    ok: bool = True
    correct: Optional[bool] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    chosen_style: str
    blocks: List[ExplanationBlock]


def _generate(payload: ExplanationRequest, session: Session) -> ExplanationResponse:
    # Path 1: exercise-based explanation
    if payload.exercise_id:
        exercise = session.exec(select(Exercise).where(Exercise.id == payload.exercise_id)).first()
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exercise not found: {payload.exercise_id}",
            )

        user_ans = "" if payload.user_answer is None else str(payload.user_answer).strip()
        correct_ans = "" if exercise.correct_answer is None else str(exercise.correct_answer).strip()
        is_correct = bool(user_ans) and user_ans == correct_ans

        explanation_text = exercise.solution_explanation or "No explanation available."

        logger.info("explanations.generate id=%s correct=%s", payload.exercise_id, is_correct)

        style = "step_by_step"
        # Try LLM first; then deterministic blocks.
        blocks = generate_explanation_blocks_llm(explanation_text, style) or generate_explanation_blocks(
            explanation_text, style, analytical_comfort=None
        )
        if exercise.hint:
            blocks.append(ExplanationBlock(style="analogy", title="Hint", content=exercise.hint))

        return ExplanationResponse(
            correct=is_correct,
            explanation=explanation_text,
            hint=exercise.hint,
            chosen_style=style,
            blocks=blocks,
        )

    # Path 2: text-only request (compat with newer FE)
    if payload.text:
        logger.info("explanations.generate text-only mode=%s", payload.mode)
        style = payload.mode if payload.mode else "big_picture"
        allowed_styles = {"step_by_step", "big_picture", "analogy", "visual", "problems", "auto"}
        if style not in allowed_styles:
            style = "big_picture"
        if style == "auto":
            style = "big_picture"

        blocks = generate_explanation_blocks_llm(payload.text, style) or generate_explanation_blocks(
            payload.text, style, analytical_comfort=None
        )

        return ExplanationResponse(
            correct=False,
            explanation=payload.text,
            hint=None,
            chosen_style=style,
            blocks=blocks,
        )

    # If neither provided, bad request
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="exercise_id or text is required",
    )


@router_api.post("/generate", response_model=ExplanationResponse)
def generate_explanation_api(payload: ExplanationRequest, session: Session = Depends(get_session)):
    return _generate(payload, session)


@router_compat.post("/generate", response_model=ExplanationResponse)
def generate_explanation_compat(payload: ExplanationRequest, session: Session = Depends(get_session)):
    return _generate(payload, session)
