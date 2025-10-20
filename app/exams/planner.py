from __future__ import annotations

import math
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import func
from sqlmodel import Session, select

from app.exams.models import (
    Exam,
    ExamTopic,
    QuestionnaireResult,
    StudyBlock,
    StudyBlockKind,
    StudyBlockStatus,
    StudyPlan,
)
from app.exams.schemas import PlannerOptions

STYLE_DEFAULT = "spaced_structured"


def split_minutes(total: int, min_block: int) -> List[int]:
    """Split minutes into chunks of at least min_block (last chunk may exceed total)."""
    if total <= min_block:
        return [max(total, min_block)]
    chunks = max(1, math.ceil(total / min_block))
    parts: List[int] = []
    remaining = total
    for index in range(chunks):
        if index == chunks - 1:
            chunk = max(min_block, remaining)
        else:
            chunk = min_block
        parts.append(chunk)
        remaining -= chunk
        if remaining <= 0:
            remaining = 0
    if remaining > 0:
        parts[-1] += remaining
    return parts


def interleave(list_a: Sequence, list_b: Sequence, ratio: float) -> List:
    """Merge two sequences honouring a ratio of A to total."""
    if not list_a:
        return list(list_b)
    if not list_b:
        return list(list_a)
    ratio = min(1.0, max(0.0, ratio))
    result: List = []
    count_a = 0
    count_b = 0
    idx_a = 0
    idx_b = 0
    while idx_a < len(list_a) or idx_b < len(list_b):
        take_a = False
        total = max(1, count_a + count_b)
        current_ratio = count_a / total
        desired = ratio
        if idx_a < len(list_a):
            if idx_b >= len(list_b):
                take_a = True
            else:
                take_a = current_ratio <= desired
        if take_a and idx_a < len(list_a):
            result.append(list_a[idx_a])
            idx_a += 1
            count_a += 1
        elif idx_b < len(list_b):
            result.append(list_b[idx_b])
            idx_b += 1
            count_b += 1
        else:
            break
    return result


def _next_plan_version(session: Session, exam_id) -> int:
    query = select(func.max(StudyPlan.version)).where(StudyPlan.exam_id == exam_id)
    result = session.exec(query).first()
    if result is None:
        return 1
    if isinstance(result, tuple):
        value = result[0]
    elif hasattr(result, "_mapping"):
        value = list(result)[0]
    else:
        value = result
    return int(value or 0) + 1


def _difficulty_for_topic(topic: ExamTopic) -> int:
    difficulty = topic.priority or 2
    if topic.est_minutes >= 180:
        difficulty = max(difficulty, 3)
    elif topic.est_minutes >= 120:
        difficulty = max(difficulty, 2)
    return min(3, max(1, difficulty))


def _minutes_breakdown(topic: ExamTopic, min_block: int) -> Tuple[int, int, int]:
    total = max(topic.est_minutes, min_block * 3)
    learn = max(min_block, int(total * 0.5))
    review = max(min_block, int(total * 0.3))
    drill = max(min_block, total - learn - review)
    if drill < min_block:
        drill = min_block
    overshoot = learn + review + drill - total
    if overshoot > 0:
        drill = max(min_block, drill - overshoot)
    return learn, review, drill


def _style_spacing(style: str) -> Tuple[int, int]:
    if style == "cram_then_revise":
        return 2, 1
    if style == "interleaved_hands_on":
        return 1, 2
    if style == "theory_first":
        return 2, 3
    return 1, 3


def _initial_day_order(style: str, days: List[date]) -> Iterable[int]:
    if style == "interleaved_hands_on":
        for idx in range(len(days)):
            yield idx
    while True:
        yield 0


def _mock_minutes(min_block: int) -> int:
    baseline = max(min_block, 75)
    return min(90, max(min_block, baseline))


def _ensure_day_sequence(start_day: date, end_day: date) -> List[date]:
    if start_day > end_day:
        return [start_day]
    days: List[date] = []
    cursor = start_day
    while cursor <= end_day:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def build_plan(
    session: Session,
    exam: Exam,
    topics: Sequence[ExamTopic],
    style: str,
    opts: PlannerOptions,
) -> Tuple[StudyPlan, List[StudyBlock]]:
    style = style if style in {"spaced_structured", "cram_then_revise", "interleaved_hands_on", "theory_first"} else STYLE_DEFAULT
    today = datetime.utcnow().date()
    buffer = max(0, opts.buffer_days)
    horizon = exam.exam_at.date() - timedelta(days=buffer)
    working_days = _ensure_day_sequence(today, max(today, horizon))

    day_usage: Dict[date, int] = {day: 0 for day in working_days}
    plan = StudyPlan(
        exam_id=exam.id,
        version=_next_plan_version(session, exam.id),
        strategy=style,
    )
    session.add(plan)
    session.flush()

    blocks: List[StudyBlock] = []
    day_pointer = _initial_day_order(style, working_days)
    next_day_index = next(day_pointer, 0)
    learn_day_index: Dict[UUID, int] = {}

    sorted_topics = sorted(topics, key=lambda t: (t.priority or 2, t.name.lower()))
    if style == "interleaved_hands_on":
        random.shuffle(sorted_topics)

    review_gap, drill_gap = _style_spacing(style)

    def schedule_block(
        topic: Optional[ExamTopic],
        kind: StudyBlockKind,
        minutes: int,
        earliest_index: int,
        status: StudyBlockStatus = StudyBlockStatus.SCHEDULED,
    ) -> int:
        nonlocal blocks
        index = max(0, min(earliest_index, len(working_days) - 1))
        while index < len(working_days):
            day = working_days[index]
            if day_usage[day] + minutes <= opts.daily_cap_min or index == len(working_days) - 1:
                break
            index += 1
        index = min(index, len(working_days) - 1)
        day = working_days[index]
        day_usage[day] += minutes
        topic_id = topic.id if topic else None
        topic_name = topic.name if topic else exam.title
        difficulty = _difficulty_for_topic(topic) if topic else 2
        block = StudyBlock(
            plan_id=plan.id,
            exam_id=exam.id,
            topic_id=topic_id,
            day=day,
            start=None,
            minutes=minutes,
            kind=kind,
            topic=topic_name,
            difficulty=difficulty,
            status=status,
        )
        session.add(block)
        blocks.append(block)
        return index

    for topic in sorted_topics:
        learn_minutes, review_minutes, drill_minutes = _minutes_breakdown(topic, opts.min_block)
        if style == "interleaved_hands_on":
            next_index = next_day_index % len(working_days)
            next_day_index += 1
        else:
            next_index = 0
        learn_index = schedule_block(topic, StudyBlockKind.LEARN, learn_minutes, next_index)
        learn_day_index[topic.id] = learn_index

        if style == "cram_then_revise":
            review_target = max(len(working_days) - 3, learn_index + review_gap)
        elif style == "theory_first":
            review_target = min(len(working_days) - 1, learn_index + max(1, review_gap + 1))
        else:
            review_target = min(len(working_days) - 1, learn_index + review_gap)
        review_index = schedule_block(topic, StudyBlockKind.REVIEW, review_minutes, review_target)

        if style == "cram_then_revise":
            drill_target = max(len(working_days) - 2, review_index + drill_gap)
        elif style == "theory_first":
            drill_target = min(len(working_days) - 1, max(review_index + drill_gap, len(working_days) - 2))
        else:
            drill_target = min(len(working_days) - 1, review_index + drill_gap)

        drill_chunks = [drill_minutes]
        if style == "interleaved_hands_on" and drill_minutes >= opts.min_block * 2:
            drill_chunks = split_minutes(drill_minutes, opts.min_block)

        for offset, chunk in enumerate(drill_chunks):
            drill_index = schedule_block(
                topic,
                StudyBlockKind.DRILL,
                chunk,
                min(len(working_days) - 1, drill_target + offset),
            )
            drill_target = drill_index + 1

    mock_count = max(0, opts.mock_count)
    if mock_count:
        mock_minutes = _mock_minutes(opts.min_block)
        last_week_start = max(0, len(working_days) - 7)
        span = len(working_days) - last_week_start
        spacing = max(1, span // mock_count) if span else 1
        target_indices = [min(len(working_days) - 1, last_week_start + i * spacing) for i in range(mock_count)]
        seen = set()
        for idx in target_indices:
            if idx in seen:
                idx = min(len(working_days) - 1, idx + 1)
            seen.add(idx)
            schedule_block(None, StudyBlockKind.MOCK, mock_minutes, idx)

    session.flush()
    return plan, blocks


def latest_questionnaire_style(session: Session, exam_id) -> Optional[str]:
    stmt = (
        select(QuestionnaireResult)
        .where(QuestionnaireResult.exam_id == exam_id)
        .order_by(QuestionnaireResult.created_at.desc())
    )
    result = session.exec(stmt).first()
    if result is None:
        return None
    if isinstance(result, QuestionnaireResult):
        return result.style
    if isinstance(result, tuple):
        record = result[0]
        if isinstance(record, QuestionnaireResult):
            return record.style
    return None


def reflow_plan(session: Session, plan_id) -> None:
    """Simple reflow: move skipped blocks forward and trim if necessary."""
    plan = session.get(StudyPlan, plan_id)
    if not plan:
        return
    blocks = session.exec(
        select(StudyBlock).where(StudyBlock.plan_id == plan.id).order_by(StudyBlock.day.asc())
    ).all()
    if not blocks:
        return
    today = datetime.utcnow().date()
    carry_minutes: Dict[str, int] = defaultdict(int)
    for block in blocks:
        if block.day < today and block.status != StudyBlockStatus.DONE:
            carry_minutes[block.topic] += block.minutes
            block.status = StudyBlockStatus.SKIPPED
            block.actual_minutes = 0

    if not carry_minutes:
        return

    future_blocks = [block for block in blocks if block.day >= today and block.status == StudyBlockStatus.SCHEDULED]
    for block in future_blocks:
        topic_minutes = carry_minutes.get(block.topic)
        if not topic_minutes:
            continue
        reduction = min(block.minutes // 2, topic_minutes)
        if reduction <= 0:
            continue
        block.minutes = max(15, block.minutes - reduction)
        carry_minutes[block.topic] = max(0, topic_minutes - reduction)

    session.flush()
