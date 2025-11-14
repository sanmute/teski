from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session

from app.learner.models import LearnerProfile
from app.learner.service import get_or_default_profile
from app.study.models import StudyReflection, StudySession
from app.study.schemas import (
    SessionPhaseStep,
    SessionPlan,
    StudySessionCompleteRequest,
    StudySessionCompleteResponse,
    StudySessionDetailResponse,
    StudySessionStartResponse,
)
from app.tasks.models import Task, TaskBlock

ALLOWED_TIME_FEELINGS = {"too_short", "just_right", "too_long"}


def get_task_and_block(db: Session, task_block_id: int) -> Tuple[Task, TaskBlock]:
    """Fetch a block and its parent task or raise 404."""
    block = db.get(TaskBlock, task_block_id)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task_block_not_found")
    task = db.get(Task, block.task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task_not_found")
    return task, block


def _phase_step(step_id: str, label: str, description: Optional[str] = None) -> SessionPhaseStep:
    return SessionPhaseStep(id=step_id, label=label, description=description)


def generate_session_plans(
    profile: LearnerProfile, block_label: str, duration_minutes: int
) -> tuple[SessionPlan, SessionPlan, SessionPlan]:
    """Generate deterministic session plans informed by the learner profile."""
    long_reaction = (profile.long_assignment_reaction or "").lower()
    practice_style = (profile.practice_style or "mixed").lower()
    explanation = (profile.explanation_style or "").lower()

    prepare_steps = [
        _phase_step("prep_goal", "Clarify your goal", "Write one sentence describing success."),
        _phase_step("prep_materials", "Open needed materials", "Slides, notes, calculator, etc."),
        _phase_step("prep_focus", "Remove distractions", "Silence notifications for this block."),
    ]
    if long_reaction in {"overwhelmed", "procrastinate"}:
        prepare_steps.insert(
            0, _phase_step("prep_breathe", "Take a calming breath", "Remind yourself this is a short block.")
        )

    focus_steps: list[SessionPhaseStep] = []
    if long_reaction == "procrastinate":
        focus_steps.append(
            _phase_step("focus_microstart", "Just start", "Do a 2-minute micro-task to gain momentum.")
        )
    if practice_style == "short_bursts":
        focus_steps += [
            _phase_step("focus_sprint1", "Sprint 1", "Work intensely for 5–7 minutes."),
            _phase_step("focus_check", "Quick check", "Note progress or blockers."),
            _phase_step("focus_sprint2", "Sprint 2", "Resume with the next tiny chunk."),
        ]
    elif practice_style == "long_sessions":
        focus_steps += [
            _phase_step("focus_warmup", "Warm-up", "Review key ideas before diving deep."),
            _phase_step("focus_deepdive", "Deep dive", "Stay with one complex problem for most of the block."),
        ]
    else:  # mixed/default
        focus_steps += [
            _phase_step("focus_quickreview", "Quick review", "Skim notes or outline the approach."),
            _phase_step("focus_build", "Build/solve", "Spend most of the block producing work."),
        ]

    # Explanation-style hints
    if explanation == "step_by_step":
        focus_steps.append(
            _phase_step("focus_steps", "Micro-steps", "Break the current problem into the smallest steps possible.")
        )
    elif explanation == "big_picture":
        focus_steps.append(
            _phase_step("focus_overview", "Big-picture check", "Summarize how this block fits into the course.")
        )
    elif explanation == "analogy":
        focus_steps.append(
            _phase_step("focus_analogy", "Analogy", "Relate the concept to a simpler scenario before solving.")
        )
    elif explanation == "visual":
        focus_steps.append(
            _phase_step("focus_visual", "Sketch", "Draw a quick diagram or outline of what you're working on.")
        )
    elif explanation == "problems":
        focus_steps.append(
            _phase_step("focus_example", "Example first", "Run through a concrete example to prime your thinking.")
        )

    if long_reaction == "motivated":
        focus_steps.append(
            _phase_step("focus_push", "Stretch goal", "Tackle a slightly harder variation if time remains.")
        )

    close_steps = [
        _phase_step("close_summary", "Summarize", "Write 2–3 bullets describing what you accomplished."),
        _phase_step("close_mark", "Log progress", "Mark this block done in Teski / your tracker."),
        _phase_step("close_next", "Next step", "Note one question or action for the next session."),
    ]
    if long_reaction == "overwhelmed":
        close_steps.insert(
            0, _phase_step("close_ack", "Acknowledge effort", "Give yourself credit for showing up.")
        )

    prepare_plan = SessionPlan(phase="prepare", title="Get ready", steps=prepare_steps)
    focus_plan = SessionPlan(phase="focus", title=f"Focus on {block_label.lower()}", steps=focus_steps)
    close_plan = SessionPlan(phase="close", title="Wrap up", steps=close_steps)
    return prepare_plan, focus_plan, close_plan


def _session_to_response(
    session_obj: StudySession,
    task: Task,
    block: TaskBlock,
    plans: tuple[SessionPlan, SessionPlan, SessionPlan],
) -> StudySessionStartResponse:
    prepare, focus, close = plans
    base = {
        "session_id": session_obj.id,
        "task_id": task.id,
        "task_block_id": block.id,
        "block_label": block.label,
        "block_duration_minutes": block.duration_minutes,
        "task_title": task.title,
        "course": task.course,
        "kind": task.kind,
        "planned_duration_minutes": session_obj.planned_duration_minutes,
        "plan_prepare": prepare,
        "plan_focus": focus,
        "plan_close": close,
    }
    return StudySessionStartResponse(**base)


def create_study_session(
    db: Session,
    user_id: UUID,
    task_block_id: int,
    goal_text: Optional[str] = None,
) -> StudySessionStartResponse:
    """Create a new study session anchored to a task block with an adaptive plan."""
    profile = get_or_default_profile(db, user_id)
    task, block = get_task_and_block(db, task_block_id)
    if task.user_id != user_id or block.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="task_block_not_owned")

    session_obj = StudySession(
        user_id=user_id,
        task_id=task.id,
        task_block_id=block.id,
        started_at=datetime.utcnow(),
        planned_duration_minutes=block.duration_minutes,
        status="active",
        goal_text=goal_text,
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    plans = generate_session_plans(profile, block.label, block.duration_minutes)
    return _session_to_response(session_obj, task, block, plans)


def get_study_session_detail(
    db: Session,
    user_id: UUID,
    session_id: int,
) -> StudySessionDetailResponse:
    """Return full details for a study session."""
    session_obj = db.get(StudySession, session_id)
    if session_obj is None or session_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="study_session_not_found")
    task, block = get_task_and_block(db, session_obj.task_block_id)
    profile = get_or_default_profile(db, user_id)
    plans = generate_session_plans(profile, block.label, block.duration_minutes)

    response = StudySessionDetailResponse(
        **_session_to_response(session_obj, task, block, plans).model_dump(),
        status=session_obj.status,
        started_at=session_obj.started_at,
        ended_at=session_obj.ended_at,
    )
    return response


def complete_study_session(
    db: Session,
    user_id: UUID,
    session_id: int,
    req: StudySessionCompleteRequest,
) -> StudySessionCompleteResponse:
    """Mark a study session as completed and store reflection metadata."""
    session_obj = db.get(StudySession, session_id)
    if session_obj is None or session_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="study_session_not_found")

    if session_obj.status == "completed":
        return StudySessionCompleteResponse(session_id=session_obj.id, status=session_obj.status)

    now = datetime.utcnow()
    session_obj.ended_at = session_obj.ended_at or now
    if req.actual_duration_minutes:
        session_obj.actual_duration_minutes = req.actual_duration_minutes
    elif session_obj.started_at and session_obj.ended_at:
        delta_minutes = max(1, int((session_obj.ended_at - session_obj.started_at).total_seconds() // 60))
        session_obj.actual_duration_minutes = delta_minutes
    session_obj.status = "completed"
    session_obj.updated_at = now

    if req.time_feeling and req.time_feeling not in ALLOWED_TIME_FEELINGS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_time_feeling")

    reflection = StudyReflection(
        session_id=session_obj.id,
        user_id=user_id,
        goal_completed=req.goal_completed,
        perceived_difficulty=req.perceived_difficulty,
        time_feeling=req.time_feeling,
        notes=req.notes,
    )
    db.add(reflection)
    db.add(session_obj)
    db.commit()
    return StudySessionCompleteResponse(session_id=session_obj.id, status=session_obj.status)
