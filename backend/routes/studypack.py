from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from ..db import get_session
from ..models_studypack import StudyPack
from ..schemas_studypack import StudyPackOut, Resource, PracticeItem
from ..services.studypack import build_study_pack_for_task
from pydantic import BaseModel
from ..settings import DEFAULT_TIMEZONE
import json

router = APIRouter(prefix="/api/study-pack", tags=["study-pack"])

class BuildStudyPackRequest(BaseModel):
    taskId: str
    persona: str = "teacher"
    escalation: str = "calm"

@router.post("/build", response_model=StudyPackOut)
def build(request: BuildStudyPackRequest, session: Session = Depends(get_session)):
    try:
        data = build_study_pack_for_task(session, request.taskId, request.persona, request.escalation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return StudyPackOut(
        taskId=data["taskId"],
        topic=data["topic"],
        resources=[Resource(**r) for r in data["resources"]],
        practice=[PracticeItem(**p) for p in data["practice"]],
        brief_speech=data["brief_speech"],
        cta=data["cta"],
        created_at=datetime.fromisoformat(data["created_at"]).astimezone(DEFAULT_TIMEZONE)
    )


@router.get("/{taskId}", response_model=StudyPackOut)
def get_pack(taskId: str, session: Session = Depends(get_session)):
    sp = session.exec(select(StudyPack).where(StudyPack.task_id == taskId)).first()
    if not sp:
        try:
            data = build_study_pack_for_task(session, taskId)
            return StudyPackOut(
                taskId=data["taskId"],
                topic=data["topic"],
                resources=[Resource(**r) for r in data["resources"]],
                practice=[PracticeItem(**p) for p in data["practice"]],
                brief_speech=data["brief_speech"],
                cta=data["cta"],
                created_at=datetime.fromisoformat(data["created_at"]).astimezone(DEFAULT_TIMEZONE)
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # Ensure sp.created_at is offset-aware
    created_at = sp.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        created_at = created_at.astimezone(DEFAULT_TIMEZONE)

    # Calculate expiration time
    expiration_time = created_at + timedelta(hours=sp.ttl_hours)

    # Compare with current time; rebuild automatically if stale
    if expiration_time < datetime.now(DEFAULT_TIMEZONE):
        data = build_study_pack_for_task(session, taskId)
        return StudyPackOut(
            taskId=data["taskId"],
            topic=data["topic"],
            resources=[Resource(**r) for r in data["resources"]],
            practice=[PracticeItem(**p) for p in data["practice"]],
            brief_speech=data["brief_speech"],
            cta=data["cta"],
            created_at=datetime.fromisoformat(data["created_at"]).astimezone(DEFAULT_TIMEZONE)
        )

    from json import loads
    return StudyPackOut(
        taskId=sp.task_id,
        topic=sp.topic,
        resources=[Resource(**r) for r in loads(sp.resources_json)],
        practice=[PracticeItem(**p) for p in loads(sp.practice_json)],
        brief_speech=sp.brief_speech,
        cta=sp.cta,
        created_at=sp.created_at.astimezone(DEFAULT_TIMEZONE) if sp.created_at.tzinfo else sp.created_at.replace(tzinfo=DEFAULT_TIMEZONE)
    )
