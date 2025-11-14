from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.study.schemas import (
    StudySessionCompleteRequest,
    StudySessionCompleteResponse,
    StudySessionCreateRequest,
    StudySessionDetailResponse,
    StudySessionStartResponse,
)
from app.study.service import (
    complete_study_session,
    create_study_session,
    get_study_session_detail,
)

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/sessions/start", response_model=StudySessionStartResponse)
def start_session(
    payload: StudySessionCreateRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> StudySessionStartResponse:
    return create_study_session(session, user.id, payload.task_block_id, payload.goal_text)


@router.get("/sessions/{session_id}", response_model=StudySessionDetailResponse)
def get_session_detail(
    session_id: int,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> StudySessionDetailResponse:
    return get_study_session_detail(session, user.id, session_id)


@router.post("/sessions/{session_id}/complete", response_model=StudySessionCompleteResponse)
def complete_session(
    session_id: int,
    payload: StudySessionCompleteRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> StudySessionCompleteResponse:
    return complete_study_session(session, user.id, session_id, payload)
