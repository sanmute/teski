from __future__ import annotations

import re
import logging
import os
from typing import Callable, List

from app.learner.models import LearnerProfile
from app.feedback.router import call_llm

from .schemas import ExplanationBlock, ExplanationResponse

ALLOWED_STYLES = {"step_by_step", "big_picture", "analogy", "visual", "problems"}
LOW_COMFORT_PREFIX = "Let's go slowly through this:"
HIGH_COMFORT_PREFIX = "Here’s the core idea in a compact form:"
logger = logging.getLogger(__name__)


def _detect_explanations_model() -> str:
    """Pick a sensible default model based on available provider keys."""
    explicit = os.getenv("EXPLANATIONS_MODEL")
    if explicit:
        return explicit
    if os.getenv("OPENAI_API_KEY"):
        return "mini:gpt4_1"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "mini:haiku4_5"
    # Fall back to local inference hook so installations without hosted keys can still work.
    return "local:llama70b"


EXPLANATIONS_MODEL = _detect_explanations_model()


def choose_style(profile: LearnerProfile, requested_mode: str | None) -> str:
    """Return the explanation style honoring explicit requests and profile defaults."""
    requested = (requested_mode or "auto").lower()
    if requested != "auto" and requested in ALLOWED_STYLES:
        return requested
    profile_style = (profile.explanation_style or "big_picture").lower()
    if profile_style not in ALLOWED_STYLES:
        return "big_picture"
    return profile_style


def generate_explanation_blocks(text: str, style: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    """Transform the base text into one or more explanation blocks for the chosen style."""
    style = style if style in ALLOWED_STYLES else "big_picture"
    builder = _STYLE_BUILDERS[style]
    blocks = builder(text.strip(), analytical_comfort)
    return blocks


async def generate_personalized_explanation(
    text: str,
    profile: LearnerProfile,
    requested_mode: str | None,
) -> ExplanationResponse:
    """Tie all personalization rules together for a single request."""
    style = choose_style(profile, requested_mode)

    try:
        llm_text = await _generate_with_llm(text, style, profile)
        blocks = _blocks_from_llm(style, llm_text)
        if not blocks:
            raise ValueError("empty_llm_response")
    except Exception as exc:  # pragma: no cover - graceful fallback when LLM unavailable
        logger.warning("Falling back to deterministic explanation blocks: %s", exc)
        blocks = generate_explanation_blocks(text, style, profile.analytical_comfort)

    return ExplanationResponse(chosen_style=style, blocks=blocks)


async def _generate_with_llm(text: str, style: str, profile: LearnerProfile) -> str:
    tone = (profile.communication_style or "supportive").replace("_", " ")
    comfort = profile.analytical_comfort or 3
    comfort_hint = (
        "Keep the language friendly and concrete." if comfort <= 2 else "You can be concise and assume background knowledge."
    )
    persona = profile.long_assignment_reaction or "balanced"
    prompt = (
        "You are Teski, a study companion."
        f" The student asked: "
        f"{text}\n"
        f"Produce a {style.replace('_', ' ')} explanation with 2-3 short paragraphs."
        f" Tone: {tone}. {comfort_hint}"
        f" Focus on actionable understanding and, when useful, include a quick example tied to the prompt."
        f" The user tends to react to long tasks as '{persona}', so keep motivation in mind."
        " Do NOT use LaTeX or math markup—write plain text descriptions only."
    )
    return await call_llm(EXPLANATIONS_MODEL, prompt, "en")


def _blocks_from_llm(style: str, text: str) -> List[ExplanationBlock]:
    cleaned = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if not cleaned and text.strip():
        cleaned = [text.strip()]

    titles = {
        "step_by_step": ["Guided steps"],
        "big_picture": ["Big picture", "Details"],
        "analogy": ["Analogy", "Formal view"],
        "visual": ["Visual outline"],
        "problems": ["Example", "How to reason"],
    }

    desired_blocks = titles.get(style, ["Explanation"])
    blocks: List[ExplanationBlock] = []

    if len(cleaned) == 1 or len(desired_blocks) == 1:
        content = "\n\n".join(cleaned) if cleaned else text
        blocks.append(ExplanationBlock(style=style, title=desired_blocks[0], content=content.strip()))
        return blocks

    # Map each cleaned paragraph to expected block titles
    for idx, title in enumerate(desired_blocks):
        paragraph = cleaned[idx] if idx < len(cleaned) else ""
        if not paragraph and cleaned:
            paragraph = cleaned[-1]
        blocks.append(ExplanationBlock(style=style, title=title, content=paragraph.strip()))
    return blocks


def _build_step_by_step(text: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text]
    lines = [f"Step {idx + 1}: {sentence.strip()}" for idx, sentence in enumerate(sentences) if sentence.strip()]
    content = "\n".join(lines) or f"Step 1: {text}"
    content = _apply_comfort_prefix(content, analytical_comfort)
    return [
        ExplanationBlock(style="step_by_step", title="Step-by-step explanation", content=content),
    ]


def _build_big_picture(text: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    summary = _shorten_text(text, max_sentences=2)
    summary_content = _apply_comfort_prefix(summary, analytical_comfort)
    details_content = text
    return [
        ExplanationBlock(style="big_picture", title="High-level summary", content=summary_content),
        ExplanationBlock(style="big_picture", title="Details", content=details_content),
    ]


def _build_analogy(text: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    simplified = _shorten_text(text, max_sentences=2)
    analogy_line = f"Think of it like this: {simplified}"
    analogy_line = _apply_comfort_prefix(analogy_line, analytical_comfort)
    formal_line = text
    return [
        ExplanationBlock(style="analogy", title="Analogy", content=analogy_line),
        ExplanationBlock(style="analogy", title="Formal explanation", content=formal_line),
    ]


def _build_visual(text: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text]
    lines = []
    if sentences:
        lines.append(f"• Main idea: {sentences[0]}")
    for detail in sentences[1:]:
        lines.append(f"  • Detail: {detail}")
    outline = "\n".join(lines) if lines else text
    outline = _apply_comfort_prefix(outline, analytical_comfort)
    return [
        ExplanationBlock(style="visual", title="Visual outline", content=outline),
    ]


def _build_problems(text: str, analytical_comfort: int | None) -> List[ExplanationBlock]:
    simplified = _shorten_text(text, max_sentences=2)
    example = f"Example: Suppose we apply this idea to a simple case. Then {simplified}"
    example = _apply_comfort_prefix(example, analytical_comfort)
    explanation = text
    return [
        ExplanationBlock(style="problems", title="Example", content=example),
        ExplanationBlock(style="problems", title="Explanation", content=explanation),
    ]


def _split_sentences(text: str) -> List[str]:
    parts = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    return parts


def _shorten_text(text: str, max_sentences: int = 2) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text
    return " ".join(sentences[:max_sentences])


def _apply_comfort_prefix(content: str, analytical_comfort: int | None) -> str:
    if analytical_comfort is None or analytical_comfort == 3:
        return content
    if analytical_comfort <= 2:
        return f"{LOW_COMFORT_PREFIX}\n{content}"
    if analytical_comfort >= 4:
        return f"{HIGH_COMFORT_PREFIX}\n{content}"
    return content


_STYLE_BUILDERS: dict[str, Callable[[str, int | None], List[ExplanationBlock]]] = {
    "step_by_step": _build_step_by_step,
    "big_picture": _build_big_picture,
    "analogy": _build_analogy,
    "visual": _build_visual,
    "problems": _build_problems,
}
