from __future__ import annotations

import math
from typing import List
from uuid import UUID

from sqlmodel import Session

from app.learner.models import LearnerProfile
from app.learner.service import get_or_default_profile
from app.models import _utcnow

from .models import Task, TaskBlock
from .schemas import TaskCreate

BIAS_MULTIPLIERS = {
    "underestimates_heavily": 1.4,
    "underestimates_slightly": 1.2,
    "accurate": 1.0,
    "overestimates": 0.9,
}

REACTION_CHUNK_RANGES = {
    "overwhelmed": (20, 25),
    "procrastinate": (20, 30),
    "motivated": (40, 60),
    "stressful": (25, 35),
}

PRACTICE_STYLE_TWEAKS = {
    "short_bursts": (-5, -5),
    "long_sessions": (10, 15),
}


def create_task(session: Session, user_id: UUID, payload: TaskCreate) -> Task:
    """Persist a new task for the user."""
    now = _utcnow()
    task = Task(
        user_id=user_id,
        title=payload.title,
        course=payload.course,
        kind=payload.kind,
        due_at=payload.due_at,
        base_estimated_minutes=payload.base_estimated_minutes,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def create_task_with_blocks(session: Session, user_id: UUID, payload: TaskCreate) -> tuple[Task, List[TaskBlock], LearnerProfile]:
    """Convenience helper that creates a task and immediately generates blocks."""
    profile = get_or_default_profile(session, user_id)
    task = create_task(session, user_id, payload)
    blocks = generate_blocks_for_task(session, task, profile)
    return task, blocks, profile


def compute_personalized_minutes(task: Task, profile: LearnerProfile) -> int:
    multiplier = BIAS_MULTIPLIERS.get(profile.time_estimation_bias or "accurate", 1.0)
    return max(5, int(math.ceil(task.base_estimated_minutes * multiplier)))


def generate_blocks_for_task(session: Session, task: Task, profile: LearnerProfile) -> List[TaskBlock]:
    """Create TaskBlock rows that reflect the learner's preferences."""
    total_minutes = compute_personalized_minutes(task, profile)
    block_specs = _plan_block_sequence(total_minutes, profile)
    blocks: List[TaskBlock] = []
    for spec in block_specs:
        block = TaskBlock(
            task_id=task.id,
            user_id=task.user_id,
            start_at=None,
            duration_minutes=spec["duration"],
            label=spec["label"],
            created_at=_utcnow(),
        )
        session.add(block)
        blocks.append(block)
    session.commit()
    for block in blocks:
        session.refresh(block)
    return blocks


def _plan_block_sequence(total_minutes: int, profile: LearnerProfile) -> List[dict[str, object]]:
    base_range = _base_range_for_profile(profile)
    practice_style = profile.practice_style or "mixed"
    remaining = total_minutes
    blocks: List[dict[str, object]] = []

    starter_allocated = False
    if (profile.long_assignment_reaction or "") == "procrastinate":
        duration = min(remaining, 15)
        duration = max(10, duration)
        blocks.append({"duration": duration, "label": "Starter block"})
        remaining -= duration
        starter_allocated = True

    pattern = _duration_pattern(base_range, practice_style)
    idx = 0
    while remaining > 0 and pattern:
        target = pattern[idx % len(pattern)]
        duration = min(target, remaining) if remaining < target else target
        label = "Focus block"
        remaining -= duration
        blocks.append({"duration": duration, "label": label})
        idx += 1

    if not blocks:
        blocks.append({"duration": total_minutes, "label": "Focus block"})
    elif len(blocks) > 1:
        blocks[-1]["label"] = "Review block"
        if starter_allocated and len(blocks) > 2:
            blocks[1]["label"] = "Focus block"

    return blocks


def _base_range_for_profile(profile: LearnerProfile) -> tuple[int, int]:
    reaction = profile.long_assignment_reaction or "stressful"
    base = REACTION_CHUNK_RANGES.get(reaction, REACTION_CHUNK_RANGES["stressful"])
    tweak = PRACTICE_STYLE_TWEAKS.get(profile.practice_style or "", (0, 0))
    low = max(10, base[0] + tweak[0])
    high = max(low + 5, base[1] + tweak[1])
    return (low, high)


def _duration_pattern(base_range: tuple[int, int], practice_style: str) -> List[int]:
    if practice_style == "mixed":
        short = max(10, base_range[0])
        long = max(short + 5, base_range[1])
        return [short, long]
    if practice_style == "long_sessions":
        return [base_range[1]]
    if practice_style == "short_bursts":
        return [base_range[0]]
    return [int(sum(base_range) / 2)]
