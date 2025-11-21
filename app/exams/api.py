from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.analytics import log as log_event
from app.config import get_settings
from app.db import get_session
from app.exams.models import (
    Exam,
    ExamTopic,
    QuestionnaireResult,
    StudyBlock,
    StudyBlockKind,
    StudyBlockStatus,
    StudyPlan,
)
from app.exams.planner import build_plan, interleave, latest_questionnaire_style, reflow_plan
from app.exams.questionnaire import STYLES, score_questionnaire
from app.exams.schemas import (
    AgendaItem,
    BlockOut,
    ExamIn,
    ExamOut,
    PlanOut,
    PlanProgressIn,
    PlannerOptions,
    QuestionnaireIn,
    QuestionnaireOut,
    TopicIn,
    TopicOut,
)
from app.models import Mistake, User
from app.scheduler import get_next_reviews, schedule_from_mistake
from app.timeutil import DEFAULT_TZ, user_day_bounds
from app.xp import award as award_xp

exam_router = APIRouter(prefix="/exam", tags=["exam"])


def _get_exam(session: Session, exam_id: UUID) -> Exam:
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="exam_not_found")
    return exam


def _get_plan(session: Session, exam_id: UUID) -> Optional[StudyPlan]:
    stmt = (
        select(StudyPlan)
        .where(StudyPlan.exam_id == exam_id)
        .order_by(StudyPlan.created_at.desc())
    )
    return session.exec(stmt).first()


def _exam_to_out(exam: Exam) -> ExamOut:
    return ExamOut(
        id=exam.id,
        user_id=exam.user_id,
        title=exam.title,
        course=exam.course,
        exam_at=exam.exam_at,
        created_at=exam.created_at,
        target_grade=exam.target_grade,
        notes=exam.notes,
    )


def _topic_to_out(topic: ExamTopic) -> TopicOut:
    return TopicOut(
        id=topic.id,
        exam_id=topic.exam_id,
        name=topic.name,
        est_minutes=topic.est_minutes,
        priority=topic.priority,
        dependencies=list(topic.dependencies or []),
    )


def _block_to_out(block: StudyBlock) -> BlockOut:
    return BlockOut(
        id=block.id,
        plan_id=block.plan_id,
        exam_id=block.exam_id,
        topic_id=block.topic_id,
        day=block.day,
        start=block.start,
        minutes=block.minutes,
        kind=block.kind,
        topic=block.topic,
        difficulty=block.difficulty,
        status=block.status,
        actual_minutes=block.actual_minutes,
    )


def _plan_to_out(plan: StudyPlan, blocks: Iterable[StudyBlock]) -> PlanOut:
    return PlanOut(
        id=plan.id,
        exam_id=plan.exam_id,
        created_at=plan.created_at,
        version=plan.version,
        strategy=plan.strategy,
        blocks=[_block_to_out(block) for block in blocks],
    )


@exam_router.post("/create", response_model=ExamOut)
def create_exam(payload: ExamIn, session: Session = Depends(get_session)) -> ExamOut:
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    exam = Exam(
        user_id=payload.user_id,
        title=payload.title,
        course=payload.course,
        exam_at=payload.exam_at,
        target_grade=payload.target_grade,
        notes=payload.notes,
    )
    session.add(exam)
    session.commit()
    session.refresh(exam)
    log_event("exam_created", {"exam_id": str(exam.id)}, user, session=session)
    return _exam_to_out(exam)


@exam_router.post("/{exam_id}/topics", response_model=List[TopicOut])
def add_topics(
    exam_id: UUID,
    payload: List[TopicIn],
    session: Session = Depends(get_session),
) -> List[TopicOut]:
    if not payload:
        return []
    exam = _get_exam(session, exam_id)
    existing_topics = session.exec(select(ExamTopic.name).where(ExamTopic.exam_id == exam_id)).all()
    name_set = {name for (name,) in existing_topics} if existing_topics else set()

    created: List[TopicOut] = []
    for topic_payload in payload:
        if topic_payload.name in name_set:
            continue
        topic = ExamTopic(
            exam_id=exam_id,
            name=topic_payload.name,
            est_minutes=topic_payload.est_minutes,
            priority=topic_payload.priority or 2,
            dependencies=list(topic_payload.dependencies or []),
        )
        session.add(topic)
        session.flush()
        created.append(_topic_to_out(topic))
        name_set.add(topic_payload.name)

    session.commit()
    if created:
        log_event("topics_added", {"exam_id": str(exam_id), "count": len(created)}, exam.user_id, session=session)
    return created


@exam_router.post("/{exam_id}/questionnaire", response_model=QuestionnaireOut)
def submit_questionnaire(
    exam_id: UUID,
    payload: QuestionnaireIn,
    session: Session = Depends(get_session),
) -> QuestionnaireOut:
    exam = _get_exam(session, exam_id)
    output = score_questionnaire(payload)
    result = QuestionnaireResult(
        user_id=exam.user_id,
        exam_id=exam_id,
        style=output.style,
        payload={"answers": payload.answers, "weights": output.weights},
    )
    session.add(result)
    session.commit()
    log_event("questionnaire_submitted", {"exam_id": str(exam_id), "style": output.style}, exam.user_id, session=session)
    return output


def _planner_options(options: Optional[PlannerOptions]) -> PlannerOptions:
    return options or PlannerOptions()


def _collect_topics(session: Session, exam_id: UUID) -> List[ExamTopic]:
    topics = session.exec(select(ExamTopic).where(ExamTopic.exam_id == exam_id)).all()
    if not topics:
        raise HTTPException(status_code=400, detail="topics_required")
    return topics


@exam_router.post("/{exam_id}/plan", response_model=PlanOut)
def create_plan(
    exam_id: UUID,
    options: PlannerOptions = Body(default_factory=PlannerOptions),
    session: Session = Depends(get_session),
) -> PlanOut:
    exam = _get_exam(session, exam_id)
    topics = _collect_topics(session, exam_id)
    existing_plan = _get_plan(session, exam_id)
    style = latest_questionnaire_style(session, exam_id) or (existing_plan.strategy if existing_plan else STYLES[0])

    plan, blocks = build_plan(session, exam, topics, style, _planner_options(options))
    session.commit()
    log_event("plan_built", {"exam_id": str(exam_id), "plan_id": str(plan.id), "strategy": plan.strategy}, exam.user_id, session=session)
    return _plan_to_out(plan, blocks)


@exam_router.get("/{exam_id}/plan", response_model=PlanOut)
def get_plan(
    exam_id: UUID,
    session: Session = Depends(get_session),
) -> PlanOut:
    plan = _get_plan(session, exam_id)
    if not plan:
        raise HTTPException(status_code=404, detail="plan_not_found")
    blocks = session.exec(select(StudyBlock).where(StudyBlock.plan_id == plan.id).order_by(StudyBlock.day.asc())).all()
    return _plan_to_out(plan, blocks)


def _agenda_from_blocks(blocks: Iterable[StudyBlock]) -> List[AgendaItem]:
    agenda: List[AgendaItem] = []
    for block in blocks:
        agenda.append(
            AgendaItem(
                kind="study_block",
                block_id=block.id,
                topic=block.topic,
                minutes=block.minutes,
                status=block.status,
                type=block.kind.value,
            )
        )
    return agenda


@exam_router.get("/{exam_id}/today", response_model=List[AgendaItem])
def agenda_today(
    exam_id: UUID,
    user_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> List[AgendaItem]:
    exam = _get_exam(session, exam_id)
    if exam.user_id != user_id:
        raise HTTPException(status_code=403, detail="user_mismatch")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    plan = _get_plan(session, exam_id)
    if not plan:
        return []
    tz = user.timezone or DEFAULT_TZ
    start, _ = user_day_bounds(tz)
    today_local = start.date()
    blocks = session.exec(
        select(StudyBlock)
        .where(StudyBlock.plan_id == plan.id, StudyBlock.day == today_local)
        .order_by(StudyBlock.start.asc().nullsfirst(), StudyBlock.minutes.desc())
    ).all()
    agenda_blocks = _agenda_from_blocks(blocks)

    reviews = get_next_reviews(session, user, limit=10)
    review_items = [
        AgendaItem(kind="review_due", memory_id=item.id, concept=item.concept, due_at=item.due_at, type="review")
        for item in reviews
    ]

    settings = get_settings()
    if not review_items:
        return agenda_blocks
    if settings.EX_AGENDA_REVIEW_FIRST:
        return review_items + agenda_blocks
    mixed = interleave(review_items, agenda_blocks, settings.INTERLEAVE_RATIO if hasattr(settings, "INTERLEAVE_RATIO") else 0.5)
    return mixed


@exam_router.post("/block/progress", response_model=BlockOut)
def update_block_progress(
    payload: PlanProgressIn,
    session: Session = Depends(get_session),
) -> BlockOut:
    block = session.get(StudyBlock, payload.block_id)
    if not block:
        raise HTTPException(status_code=404, detail="block_not_found")
    exam = session.get(Exam, block.exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="exam_not_found")
    user = session.get(User, exam.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    if payload.status not in {StudyBlockStatus.DONE, StudyBlockStatus.SKIPPED, StudyBlockStatus.SCHEDULED}:
        raise HTTPException(status_code=400, detail="invalid_status")

    block.status = payload.status
    block.actual_minutes = payload.minutes_spent

    if payload.status == StudyBlockStatus.DONE:
        xp_awarded = award_xp(user, reason="study_block_done", base=5, session=session)
        log_event(
            "block_done",
            {"block_id": str(block.id), "plan_id": str(block.plan_id), "xp": xp_awarded},
            user,
            session=session,
        )
        if block.kind in {StudyBlockKind.DRILL, StudyBlockKind.MOCK}:
            if payload.minutes_spent is None or payload.minutes_spent < block.minutes * 0.5:
                mistake = Mistake(
                    user_id=user.id,
                    concept=block.topic,
                    raw=f"study_block:{block.id}",
                    subtype="behavioral:incomplete_block",
                )
                session.add(mistake)
                schedule_from_mistake(session, user=user, concept=block.topic)
    elif payload.status == StudyBlockStatus.SKIPPED:
        log_event(
            "block_skipped",
            {"block_id": str(block.id), "plan_id": str(block.plan_id)},
            user,
            session=session,
        )

    session.commit()
    session.refresh(block)
    return _block_to_out(block)


@exam_router.post("/{exam_id}/regenerate", response_model=PlanOut)
def regenerate_plan(
    exam_id: UUID,
    options: PlannerOptions = Body(default_factory=PlannerOptions),
    session: Session = Depends(get_session),
) -> PlanOut:
    exam = _get_exam(session, exam_id)
    topics = _collect_topics(session, exam_id)
    existing_plan = _get_plan(session, exam_id)
    done_blocks: List[StudyBlock] = []
    if existing_plan:
        done_blocks = session.exec(
            select(StudyBlock).where(
                StudyBlock.plan_id == existing_plan.id, StudyBlock.status == StudyBlockStatus.DONE
            )
        ).all()
    style = latest_questionnaire_style(session, exam_id) or (existing_plan.strategy if existing_plan else STYLES[0])
    new_plan, blocks = build_plan(session, exam, topics, style, _planner_options(options))
    for block in done_blocks:
        clone = StudyBlock(
            plan_id=new_plan.id,
            exam_id=block.exam_id,
            topic_id=block.topic_id,
            day=block.day,
            start=block.start,
            minutes=block.minutes,
            kind=block.kind,
            topic=block.topic,
            difficulty=block.difficulty,
            status=StudyBlockStatus.DONE,
            actual_minutes=block.actual_minutes,
        )
        session.add(clone)
        blocks.append(clone)

    session.flush()
    reflow_plan(session, new_plan.id)
    session.commit()
    log_event(
        "plan_built",
        {"exam_id": str(exam_id), "plan_id": str(new_plan.id), "strategy": new_plan.strategy, "regen": True},
        exam.user_id,
        session=session,
    )
    all_blocks = session.exec(select(StudyBlock).where(StudyBlock.plan_id == new_plan.id)).all()
    return _plan_to_out(new_plan, all_blocks)
