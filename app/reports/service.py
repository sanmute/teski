from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.analytics.service import _now_utc, _session_minutes
from app.institutions.models import Institution
from app.models import User
from app.reports.schemas import (
    CourseLoadItem,
    CourseLoadSection,
    InstitutionReportData,
    ReportSummary,
    Trend,
    TrendDirection,
    WeekdayDistribution,
)
from app.study.models import StudySession
from app.tasks.models import Task


def _compute_trend(current: float, previous: Optional[float]) -> Optional[Trend]:
    if previous is None:
        return None
    if previous == 0:
        direction = TrendDirection.FLAT if current == 0 else TrendDirection.UP
    else:
        if current > previous * 1.05:
            direction = TrendDirection.UP
        elif current < previous * 0.95:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.FLAT
    return Trend(current=current, previous=previous, direction=direction)


def build_institution_report_data(
    db: Session,
    institution_id: UUID,
    days: int = 30,
    include_trends: bool = True,
    min_bucket_size: int = 10,
) -> InstitutionReportData:
    now = _now_utc()
    period_end = now
    period_start = now - timedelta(days=days)

    inst = db.get(Institution, institution_id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    stmt_users = (
        select(User.id)
        .where(User.institution_id == institution_id)
        .where(User.analytics_consent == True)  # noqa: E712
    )
    user_rows = db.exec(stmt_users).all()
    user_ids: List[UUID] = []
    for row in user_rows:
        if isinstance(row, tuple):
            user_ids.append(row[0])
        else:
            user_ids.append(row)

    consenting_students = len(user_ids)
    if consenting_students < min_bucket_size:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough consenting students for aggregated report",
        )

    def _compute_period_metrics(start: datetime, end: datetime):
        stmt_sessions = (
            select(StudySession)
            .where(StudySession.user_id.in_(user_ids))
            .where(StudySession.status == "completed")
            .where(StudySession.started_at >= start)
            .where(StudySession.started_at <= end)
        )
        sessions = db.exec(stmt_sessions).all()

        total_minutes = 0
        active_user_ids: Set[UUID] = set()
        minutes_by_weekday: Dict[int, int] = {i: 0 for i in range(7)}
        minutes_by_course: Dict[Optional[str], int] = {}

        task_ids = {s.task_id for s in sessions if getattr(s, "task_id", None) is not None}
        tasks: Dict[int, Task] = {}
        if task_ids:
            task_rows = db.exec(select(Task).where(Task.id.in_(task_ids))).all()
            tasks = {task.id: task for task in task_rows}

        for session in sessions:
            minutes = _session_minutes(session)
            total_minutes += minutes
            active_user_ids.add(session.user_id)

            if session.started_at is not None:
                weekday = session.started_at.weekday()
                minutes_by_weekday[weekday] = minutes_by_weekday.get(weekday, 0) + minutes

            course_key: Optional[str] = None
            task = tasks.get(session.task_id) if session.task_id is not None else None
            if task and task.course:
                course_key = task.course

            minutes_by_course[course_key] = minutes_by_course.get(course_key, 0) + minutes

        active_students = len(active_user_ids)
        avg_minutes_per_active = float(total_minutes) / active_students if active_students > 0 else 0.0

        total_course_minutes = sum(minutes_by_course.values())
        course_items: List[CourseLoadItem] = []
        if total_course_minutes > 0:
            for cid, mins in minutes_by_course.items():
                if mins <= 0:
                    continue
                name = cid or "Unassigned"
                course_items.append(
                    CourseLoadItem(
                        course_id=cid,
                        course_name=name,
                        minutes=mins,
                        share_of_total=mins / total_course_minutes,
                    )
                )
            course_items.sort(key=lambda item: item.minutes, reverse=True)

        return {
            "total_minutes": total_minutes,
            "active_students": active_students,
            "avg_minutes_per_active": avg_minutes_per_active,
            "minutes_by_weekday": minutes_by_weekday,
            "course_items": course_items,
        }

    current = _compute_period_metrics(period_start, period_end)

    prev_metrics = None
    if include_trends:
        prev_end = period_start
        prev_start = period_start - timedelta(days=days)
        prev_metrics = _compute_period_metrics(prev_start, prev_end)

    total_minutes_trend = _compute_trend(
        current=current["total_minutes"],
        previous=prev_metrics["total_minutes"] if prev_metrics else None,
    )
    active_students_trend = _compute_trend(
        current=current["active_students"],
        previous=prev_metrics["active_students"] if prev_metrics else None,
    )

    summary = ReportSummary(
        institution_id=inst.id,
        institution_name=inst.name,
        period_start=period_start.date(),
        period_end=period_end.date(),
        consenting_students=consenting_students,
        active_students=current["active_students"],
        total_study_minutes=current["total_minutes"],
        avg_minutes_per_active_student=current["avg_minutes_per_active"],
        total_minutes_trend=total_minutes_trend,
        active_students_trend=active_students_trend,
    )

    workload = WeekdayDistribution(minutes_by_weekday=current["minutes_by_weekday"])

    course_load = CourseLoadSection(
        total_minutes=sum(item.minutes for item in current["course_items"]),
        top_courses=current["course_items"][:5],
    )

    return InstitutionReportData(
        generated_at=now,
        summary=summary,
        workload=workload,
        course_load=course_load,
    )
