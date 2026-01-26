# >>> DFE START
from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from secrets import token_hex
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException
from jinja2 import Environment, StrictUndefined
from jinja2.exceptions import TemplateError, UndefinedError
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from models_dfe import SkillMastery, SkillNode, TaskAttempt, TaskInstance, TaskTemplate, TaskTypeEnum
from schemas_dfe_tasks import TaskTemplateCreate
from settings import EWMA_ALPHA, TESKI_PARAM_SALT
from utils.evalsafe import eval_numeric_formula, eval_predicate
from utils.rand import deterministic_seed, sample_params
from services.memory import log_mistake, mark_mastered
from services.memory_v1 import classify_error_subtype, log_mistake_v1, mark_review_result
from services.memory_bridge import (
    record_mistake_dual_write,
    record_review_dual_write,
    record_xp_event,
)
from app.detectors import classify_mistake
from utils.analytics import emit

try:
    from services.leaderboard import award_points
except Exception:  # pragma: no cover - optional dependency
    award_points = None

try:
    from services.persona import get_persona
except Exception:  # pragma: no cover - optional dependency
    get_persona = None

MAX_SAMPLING_RETRIES = 25
_TEMPLATE_ENV = Environment(undefined=StrictUndefined)


def _infer_skill_title(skill_key: str) -> str:
    leaf = skill_key.split(".")[-1]
    return leaf.replace("_", " ").title()


def _render_text(template_str: str, params: Dict[str, Any]) -> str:
    try:
        template = _TEMPLATE_ENV.from_string(template_str)
        return template.render(**params)
    except (UndefinedError, TemplateError) as exc:
        raise ValueError(f"Failed to render template: {exc}") from exc


def get_or_create_skill(session: Session, key: str, title: Optional[str], graph_version: str) -> SkillNode:
    stmt = select(SkillNode).where(SkillNode.key == key, SkillNode.graph_version == graph_version)
    skill = session.exec(stmt).first()
    if skill:
        return skill
    skill = SkillNode(key=key, title=title or _infer_skill_title(key), graph_version=graph_version)
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return skill


def create_template(session: Session, payload: TaskTemplateCreate) -> TaskTemplate:
    skill = get_or_create_skill(session, payload.skill_key, None, payload.graph_version)
    template = TaskTemplate(
        code=payload.code,
        title=payload.title,
        skill_id=skill.id,
        task_type=TaskTypeEnum(payload.task_type),
        text_template=payload.text_template,
        parameters=payload.parameters,
        constraints=payload.constraints,
        answer_spec=payload.answer_spec,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def _maybe_validate_constraints(params: Dict[str, Any], constraint_expr: Optional[str]) -> bool:
    if not constraint_expr:
        return True
    try:
        return bool(eval_predicate(constraint_expr, params))
    except ValueError:
        return False


def instantiate_for_user(session: Session, template_code: str, user_id: int, force_new: bool = False) -> Tuple[TaskInstance, TaskTemplate]:
    template_stmt = select(TaskTemplate).where(TaskTemplate.code == template_code)
    template = session.exec(template_stmt).first()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")

    if not force_new:
        base_seed = str(deterministic_seed(user_id, template.code, TESKI_PARAM_SALT))
        instance_stmt = select(TaskInstance).where(
            TaskInstance.template_id == template.id,
            TaskInstance.user_id == user_id,
            TaskInstance.seed == base_seed,
        )
        existing = session.exec(instance_stmt).first()
        if existing:
            return existing, template
        rng_seed = int(base_seed)
        seed_value = base_seed
    else:
        # fresh seed path for forced regeneration
        seed_suffix = token_hex(8)
        seed_value = f"force:{seed_suffix}"
        rng_seed = deterministic_seed(user_id, f"{template.code}:{seed_suffix}", TESKI_PARAM_SALT)

    rnd = random.Random(rng_seed)
    constraint_expr = (template.constraints or {}).get("expr") if template.constraints else None

    params: Dict[str, Any] | None = None
    for _ in range(MAX_SAMPLING_RETRIES):
        candidate = sample_params(template.parameters, rnd)
        if _maybe_validate_constraints(candidate, constraint_expr):
            params = candidate
            break
    if params is None:
        raise HTTPException(status_code=400, detail="Unable to satisfy template constraints")

    rendered_text = _render_text(template.text_template, params)

    instance = TaskInstance(
        template_id=template.id,
        user_id=user_id,
        seed=seed_value,
        params=params,
        rendered_text=rendered_text,
    )
    session.add(instance)
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Failed to persist task instance") from exc
    session.refresh(instance)
    return instance, template


def _grade_numeric(spec: Dict[str, Any], params: Dict[str, Any], submitted: Any) -> bool:
    formula = spec.get("formula")
    if not formula:
        raise HTTPException(status_code=400, detail="Missing numeric grading formula")
    truth = eval_numeric_formula(formula, params)
    tolerance = float(spec.get("tolerance", 1e-6))
    try:
        submitted_value = float(submitted)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(submitted_value):
        return False
    return abs(submitted_value - truth) <= tolerance


def _grade_multiple_choice(spec: Dict[str, Any], submitted: Any) -> bool:
    correct_index = spec.get("index")
    if correct_index is None:
        raise HTTPException(status_code=400, detail="Missing correct option index")
    try:
        return int(submitted) == int(correct_index)
    except (TypeError, ValueError):
        return False


def _grade_short_text(spec: Dict[str, Any], submitted: Any) -> bool:
    expected = spec.get("answer")
    if expected is None:
        raise HTTPException(status_code=400, detail="Missing expected answer")
    return str(submitted).strip().lower() == str(expected).strip().lower()


def _compute_mastery(old_value: float, correct: bool) -> float:
    alpha = EWMA_ALPHA
    alpha = max(0.0, min(1.0, alpha))
    new_value = (1.0 - alpha) * old_value + alpha * (1.0 if correct else 0.0)
    return max(0.0, min(1.0, new_value))


def grade_and_update(session: Session, instance_id: int, user_id: int, answer: Any, latency_ms: Optional[int]) -> Tuple[bool, float]:
    instance = session.get(TaskInstance, instance_id)
    if not instance or instance.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task instance not found")

    template = session.get(TaskTemplate, instance.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Task template missing for instance")

    spec = template.answer_spec
    if template.task_type == TaskTypeEnum.NUMERIC:
        correct = _grade_numeric(spec, instance.params, answer)
    elif template.task_type == TaskTypeEnum.MULTIPLE_CHOICE:
        correct = _grade_multiple_choice(spec, answer)
    elif template.task_type == TaskTypeEnum.SHORT_TEXT:
        correct = _grade_short_text(spec, answer)
    else:
        raise HTTPException(status_code=400, detail="Unsupported task type")

    attempt = TaskAttempt(
        instance_id=instance.id,
        user_id=user_id,
        submitted_answer=answer,
        is_correct=bool(correct),
        latency_ms=latency_ms,
    )
    session.add(attempt)

    mastery_stmt = select(SkillMastery).where(
        SkillMastery.user_id == user_id,
        SkillMastery.skill_id == template.skill_id,
    )
    mastery = session.exec(mastery_stmt).first()
    prior = mastery.mastery if mastery else 0.0
    updated_value = _compute_mastery(prior, correct)
    now = datetime.now(timezone.utc)
    if mastery is None:
        mastery = SkillMastery(
            user_id=user_id,
            skill_id=template.skill_id,
            mastery=updated_value,
            updated_at=now,
        )
        session.add(mastery)
    else:
        mastery.mastery = updated_value
        mastery.updated_at = now

    session.commit()
    return bool(correct), float(updated_value)


# >>> MEMORY START
def _resolve_task_context(
    session: Session, instance_id: int
) -> Tuple[Optional["TaskInstance"], Optional["TaskTemplate"], Optional[int], Optional[str]]:
    try:
        instance = session.get(TaskInstance, instance_id)
    except Exception:
        return None, None, None, None
    if not instance:
        return None, None, None, None
    try:
        template = session.get(TaskTemplate, instance.template_id)
    except Exception:
        return instance, None, None, None
    if not template:
        return instance, None, None, None
    return instance, template, template.skill_id, template.code


# >>> DETECTORS START
def _infer_error_subtype(
    *,
    instance: Optional["TaskInstance"],
    template: Optional["TaskTemplate"],
    submitted: Any,
    correct_value: Optional[float],
) -> str:
    prompt_text = ""
    if instance and getattr(instance, "rendered_text", None):
        prompt_text = str(instance.rendered_text)

    if correct_value is not None and math.isfinite(correct_value):
        correct_str = str(correct_value)
    elif template and template.answer_spec:
        correct_str = str(template.answer_spec.get("answer") or "")
    else:
        correct_str = ""

    answer_text = "" if submitted is None else str(submitted)

    context: Dict[str, object] = {}
    if template and template.answer_spec:
        spec = template.answer_spec
        keywords = spec.get("keywords")
        if isinstance(keywords, list):
            context["concept_keywords"] = keywords
        expected_unit = spec.get("unit")
        if expected_unit:
            context["expected_unit"] = expected_unit

    subtype = classify_mistake(
        prompt_text=prompt_text,
        user_answer=answer_text,
        correct_answer=correct_str,
        context=context,
    )
    return subtype or "recall"
# <<< DETECTORS END


def grade_and_update_with_memory_v1(
    session: Session, instance_id: int, user_id: int, answer: Any, latency_ms: Optional[int]
) -> Tuple[bool, float]:
    """Grades a submission, updates mastery, and records memory signals with heuristic error subtypes."""
    correct, mastery = grade_and_update(session, instance_id, user_id, answer, latency_ms)

    instance, template, skill_id, template_code = _resolve_task_context(session, instance_id)

    concept_ref = template.code if template else template_code or "unknown"
    review_grade = 5 if correct else 2
    if correct:
        mark_mastered(session, user_id=user_id, skill_id=skill_id, template_code=template_code)
        if template_code:
            mark_review_result(session, user_id=user_id, template_code=template_code, correct=True)
        if award_points and template_code:
            try:
                from models_leaderboard import LeaderboardMember  # type: ignore

                membership = session.exec(
                    select(LeaderboardMember).where(LeaderboardMember.user_id == user_id)
                ).first()
                if membership:
                    award_points(
                        session,
                        leaderboard_id=membership.leaderboard_id,
                        user_id=user_id,
                        event_type="mastery_bonus",
                        points=5,
                        meta={"template_code": template_code},
                    )
                    emit(
                        "memory.mastery_bonus_awarded",
                        user_id,
                        {"points": 5, "template_code": template_code},
                    )
                    record_xp_event(
                        session,
                        user_id=user_id,
                        amount=5,
                        reason="mastery_bonus",
                    )
            except Exception:
                pass
    else:
        detail: Dict[str, Any] = {"latency_ms": latency_ms}
        if get_persona:
            try:
                persona = get_persona(session, "teacher")
                if persona:
                    detail["persona_copy"] = persona.display_name or persona.code
            except Exception:
                pass
        subtype = "recall"
        truth_value: Optional[float] = None
        if template and template.task_type == TaskTypeEnum.NUMERIC:
            spec = template.answer_spec or {}
            formula = spec.get("formula")
            if formula and instance is not None:
                try:
                    truth_value = float(eval_numeric_formula(formula, instance.params))
                except Exception:
                    truth_value = None
        inferred = _infer_error_subtype(
            instance=instance,
            template=template,
            submitted=answer,
            correct_value=truth_value,
        )
        subtype = inferred or classify_error_subtype(detail)
        detail["reason"] = subtype
        log_mistake(
            session,
            user_id=user_id,
            skill_id=skill_id,
            template_code=template_code,
            instance_id=instance_id,
            error_type="recall",
            detail=detail,
            error_subtype=subtype,
        )
        log_mistake_v1(
            session,
            user_id=user_id,
            skill_id=skill_id,
            template_code=template_code,
            instance_id=instance_id,
            error_type="mistake",
            error_subtype=subtype,
            detail=detail,
        )
        if template_code:
            mark_review_result(session, user_id=user_id, template_code=template_code, correct=False)
        record_mistake_dual_write(
            session,
            user_id=user_id,
            concept=concept_ref,
            subtype=subtype,
            detail=detail,
        )

    record_review_dual_write(
        session,
        user_id=user_id,
        concept=concept_ref,
        grade=review_grade,
        task_id=None,
    )

    return correct, mastery


def grade_and_update_with_memory(
    session: Session, instance_id: int, user_id: int, answer: Any, latency_ms: Optional[int]
) -> Tuple[bool, float]:
    return grade_and_update_with_memory_v1(session, instance_id, user_id, answer, latency_ms)
# <<< MEMORY END
# <<< DFE END
