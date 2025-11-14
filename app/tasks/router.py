from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.learner.models import LearnerProfile
from app.learner.service import get_or_default_profile
from app.models import _utcnow

from .models import Task, TaskBlock
from .schemas import TaskBlockRead, TaskCreate, TaskRead, TaskStatusUpdate
from .service import compute_personalized_minutes, create_task_with_blocks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead)
def create_task_endpoint(
    payload: TaskCreate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> TaskRead:
    task, blocks, profile = create_task_with_blocks(session, user.id, payload)
    return _task_to_read(task, blocks, profile)


@router.get("/upcoming", response_model=List[TaskRead])
def list_upcoming_tasks(
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> List[TaskRead]:
    profile = get_or_default_profile(session, user.id)
    stmt = (
        select(Task)
        .where(Task.user_id == user.id, Task.status == "pending")
        .order_by(Task.due_at.is_(None), Task.due_at, Task.created_at)
    )
    tasks = session.exec(stmt).all()
    task_ids = [task.id for task in tasks]
    blocks_by_task = _blocks_for_tasks(session, task_ids)
    return [_task_to_read(task, blocks_by_task.get(task.id, []), profile) for task in tasks]


@router.patch("/{task_id}/status", response_model=TaskRead)
def update_task_status(
    payload: TaskStatusUpdate,
    task_id: int = Path(..., ge=1),
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> TaskRead:
    task = session.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="task_not_found")
    task.status = payload.status
    task.updated_at = _utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    profile = get_or_default_profile(session, user.id)
    blocks = _blocks_for_tasks(session, [task.id]).get(task.id, [])
    return _task_to_read(task, blocks, profile)


def _blocks_for_tasks(session: Session, task_ids: List[int]) -> Dict[int, List[TaskBlock]]:
    if not task_ids:
        return {}
    stmt = (
        select(TaskBlock)
        .where(TaskBlock.task_id.in_(task_ids))
        .order_by(TaskBlock.created_at)
    )
    rows = session.exec(stmt).all()
    result: Dict[int, List[TaskBlock]] = {}
    for block in rows:
        result.setdefault(block.task_id, []).append(block)
    return result


def _task_to_read(task: Task, blocks: List[TaskBlock], profile: LearnerProfile) -> TaskRead:
    return TaskRead(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        course=task.course,
        kind=task.kind,
        due_at=task.due_at,
        status=task.status,
        base_estimated_minutes=task.base_estimated_minutes,
        personalized_estimated_minutes=compute_personalized_minutes(task, profile),
        created_at=task.created_at,
        updated_at=task.updated_at,
        blocks=[_block_to_read(block) for block in blocks],
    )


def _block_to_read(block: TaskBlock) -> TaskBlockRead:
    return TaskBlockRead(
        id=block.id,
        task_id=block.task_id,
        user_id=block.user_id,
        start_at=block.start_at,
        duration_minutes=block.duration_minutes,
        label=block.label,
        created_at=block.created_at,
    )
