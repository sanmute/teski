from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Set
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.analytics.schemas import (
    CourseBreakdown,
    CourseBreakdownItem,
    DailyPoint,
    DailySeries,
    Insight,
    InsightCategory,
    InsightList,
    InsightSeverity,
    InstitutionOverview,
    SummaryMetrics,
    TopCourseItem,
    WeekdayMinutes,
)
from app.institutions.models import Institution
from app.models import User as AppUser
from app.study.models import StudySession
from app.tasks.models import Task


def _now_utc() -> datetime:
    return datetime.utcnow()


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(dt: datetime) -> datetime:
    sod = _start_of_day(dt)
    return sod - timedelta(days=sod.weekday())


def _session_minutes(session: StudySession) -> int:
    if session.actual_duration_minutes:
        return max(0, int(session.actual_duration_minutes))
    if session.planned_duration_minutes:
        return max(0, int(session.planned_duration_minutes))
    if session.started_at and session.ended_at:
        delta = session.ended_at - session.started_at
        return max(0, int(delta.total_seconds() // 60))
    return 0


def compute_summary_for_user(db: Session, user_id: UUID) -> SummaryMetrics:
    now = _now_utc()
    today_start = _start_of_day(now)
    week_start = _start_of_week(now)

    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .where(StudySession.status == "completed")
        .where(StudySession.started_at >= week_start)
    )
    sessions = db.exec(stmt).all()

    today_minutes = 0
    today_blocks = 0
    week_minutes = 0
    week_blocks = 0

    for session in sessions:
        minutes = _session_minutes(session)
        week_minutes += minutes
        week_blocks += 1
        if session.started_at >= today_start:
            today_minutes += minutes
            today_blocks += 1

    streak_days = compute_streak_days(db, user_id, now)

    return SummaryMetrics(
        today_minutes=today_minutes,
        today_blocks=today_blocks,
        week_minutes=week_minutes,
        week_blocks=week_blocks,
        streak_days=streak_days,
    )


def compute_streak_days(db: Session, user_id: UUID, now: Optional[datetime] = None) -> int:
    now = now or _now_utc()
    lookback_days = 30
    start = _start_of_day(now) - timedelta(days=lookback_days - 1)

    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .where(StudySession.status == "completed")
        .where(StudySession.started_at >= start)
    )
    sessions = db.exec(stmt).all()

    minutes_by_day: Dict[date, int] = {}
    for session in sessions:
        session_date = session.started_at.date()
        minutes_by_day[session_date] = minutes_by_day.get(session_date, 0) + _session_minutes(session)

    streak = 0
    cursor = now.date()
    while True:
        minutes = minutes_by_day.get(cursor, 0)
        if minutes <= 0:
            break
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def compute_daily_series_for_user(db: Session, user_id: UUID, days: int = 14) -> DailySeries:
    now = _now_utc()
    start = _start_of_day(now) - timedelta(days=days - 1)

    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .where(StudySession.status == "completed")
        .where(StudySession.started_at >= start)
    )
    sessions = db.exec(stmt).all()

    minutes_by_day: Dict[date, int] = {}
    blocks_by_day: Dict[date, int] = {}

    for session in sessions:
        session_date = session.started_at.date()
        minutes_by_day[session_date] = minutes_by_day.get(session_date, 0) + _session_minutes(session)
        blocks_by_day[session_date] = blocks_by_day.get(session_date, 0) + 1

    days_list: list[DailyPoint] = []
    cursor = start.date()
    end_date = now.date()
    while cursor <= end_date:
        days_list.append(
            DailyPoint(
                date=cursor,
                minutes=minutes_by_day.get(cursor, 0),
                blocks=blocks_by_day.get(cursor, 0),
            )
        )
        cursor = cursor + timedelta(days=1)

    return DailySeries(days=days_list)


def compute_course_breakdown_for_user(db: Session, user_id: UUID, days: int = 7) -> CourseBreakdown:
    now = _now_utc()
    start = _start_of_day(now) - timedelta(days=days - 1)

    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .where(StudySession.status == "completed")
        .where(StudySession.started_at >= start)
    )
    sessions = db.exec(stmt).all()

    task_ids = {session.task_id for session in sessions if session.task_id is not None}
    tasks: Dict[int, Task] = {}
    if task_ids:
        tasks_result = db.exec(select(Task).where(Task.id.in_(task_ids))).all()
        tasks = {task.id: task for task in tasks_result}

    minutes_by_course: Dict[Optional[str], int] = {}
    blocks_by_course: Dict[Optional[str], int] = {}
    course_names: Dict[Optional[str], str] = {}

    for session in sessions:
        minutes = _session_minutes(session)
        task = tasks.get(session.task_id) if session.task_id is not None else None

        course_id: Optional[str] = None
        course_name = "Unassigned"

        if task and task.course:
            course_id = task.course
            course_name = task.course

        minutes_by_course[course_id] = minutes_by_course.get(course_id, 0) + minutes
        blocks_by_course[course_id] = blocks_by_course.get(course_id, 0) + 1
        course_names[course_id] = course_name

    items: list[CourseBreakdownItem] = []
    for cid, minutes in minutes_by_course.items():
        items.append(
            CourseBreakdownItem(
                course_id=cid,
                course_name=course_names.get(cid, "Unassigned"),
                minutes=minutes,
                blocks=blocks_by_course.get(cid, 0),
                on_track=None,
            )
        )

    items.sort(key=lambda item: item.minutes, reverse=True)
    return CourseBreakdown(items=items)


def generate_insights_for_user(db: Session, user_id: UUID) -> InsightList:
    summary = compute_summary_for_user(db, user_id)
    daily_series = compute_daily_series_for_user(db, user_id, days=14)
    course_breakdown = compute_course_breakdown_for_user(db, user_id, days=7)

    insights: list[Insight] = []

    if daily_series.days:
        last_days = daily_series.days[-3:]
        if all(day.minutes == 0 for day in last_days):
            insights.append(
                Insight(
                    id="no_study_last_3_days",
                    severity=InsightSeverity.warning,
                    category=InsightCategory.consistency,
                    title="You've taken a longer break",
                    message=(
                        "There has been no recorded study time in the last three days. "
                        "If this wasn't intentional rest, it might help to schedule one short, focused block today."
                    ),
                )
            )

    if summary.week_minutes < 60:
        insights.append(
            Insight(
                id="very_low_weekly_minutes",
                severity=InsightSeverity.info,
                category=InsightCategory.workload,
                title="Very light study week so far",
                message=(
                    "You have under an hour of study time recorded this week. "
                    "If deadlines are coming up, consider planning a focused block soon."
                ),
            )
        )

    if daily_series.days:
        total_minutes_14 = sum(day.minutes for day in daily_series.days)
        if total_minutes_14 > 0:
            sorted_days = sorted(daily_series.days, key=lambda d: d.minutes, reverse=True)
            top_two_minutes = sum(day.minutes for day in sorted_days[:2])
            if top_two_minutes >= 0.7 * total_minutes_14:
                insights.append(
                    Insight(
                        id="clustering_on_few_days",
                        severity=InsightSeverity.warning,
                        category=InsightCategory.timing,
                        title="Most of your studying is clustered",
                        message=(
                            "A large share of your study time in the last two weeks happened on only one or two days. "
                            "Spreading your effort into smaller, more regular blocks often makes studying feel less stressful."
                        ),
                    )
                )

    if course_breakdown.items:
        total_minutes_courses = sum(item.minutes for item in course_breakdown.items)
        if total_minutes_courses > 0:
            top = sorted(course_breakdown.items, key=lambda item: item.minutes, reverse=True)
            leader = top[0]
            leader_pct = leader.minutes / total_minutes_courses
            if leader_pct >= 0.7 and len(top) > 1:
                insights.append(
                    Insight(
                        id="single_course_dominates",
                        severity=InsightSeverity.info,
                        category=InsightCategory.balance,
                        title="Most of your time goes into one course",
                        message=(
                            f"About {int(leader_pct * 100)}% of your recent study time went into '{leader.course_name}'. "
                            "If you have other courses with upcoming deadlines, it might help to allocate some time to them as well."
                        ),
                    )
                )

    if summary.streak_days >= 5:
        insights.append(
            Insight(
                id="good_streak",
                severity=InsightSeverity.info,
                category=InsightCategory.consistency,
                title="Nice consistency",
                message=(
                    f"You've studied {summary.streak_days} days in a row. "
                    "Keeping a regular rhythm is one of the best predictors of long-term progress."
                ),
            )
        )

    if len(insights) > 4:
        insights = insights[:4]

    return InsightList(insights=insights)


def compute_institution_overview(db: Session, institution_id: UUID, min_bucket_size: int = 10) -> InstitutionOverview:
    inst = db.get(Institution, institution_id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    now = _now_utc()
    week_ago = now - timedelta(days=7)

    stmt_users = (
        select(AppUser.id)
        .where(AppUser.institution_id == institution_id)
        .where(AppUser.analytics_consent == True)  # noqa: E712
    )
    user_rows = db.exec(stmt_users).all()
    user_ids: list[UUID] = []
    for row in user_rows:
        if isinstance(row, tuple):
            user_ids.append(row[0])
        else:
            user_ids.append(row)

    total_students = len(user_ids)
    if total_students < min_bucket_size:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough consenting students for aggregated analytics",
        )

    stmt_sessions = (
        select(StudySession)
        .where(StudySession.user_id.in_(user_ids))
        .where(StudySession.status == "completed")
        .where(StudySession.started_at >= week_ago)
    )
    sessions = db.exec(stmt_sessions).all()

    total_study_minutes_last_7d = 0
    active_user_ids: Set[UUID] = set()
    minutes_by_weekday: Dict[int, int] = {i: 0 for i in range(7)}
    minutes_by_course: Dict[Optional[str], int] = {}

    task_ids = {session.task_id for session in sessions if session.task_id is not None}
    tasks: Dict[int, Task] = {}
    if task_ids:
        tasks_result = db.exec(select(Task).where(Task.id.in_(task_ids))).all()
        tasks = {task.id: task for task in tasks_result}

    for session in sessions:
        minutes = _session_minutes(session)
        total_study_minutes_last_7d += minutes
        active_user_ids.add(session.user_id)

        if session.started_at is not None:
            weekday = session.started_at.weekday()
            minutes_by_weekday[weekday] = minutes_by_weekday.get(weekday, 0) + minutes

        course_key: Optional[str] = None
        course_name = "Unassigned"
        task = tasks.get(session.task_id) if session.task_id is not None else None
        if task and task.course:
            course_key = task.course
            course_name = task.course
        minutes_by_course[course_key or course_name] = minutes_by_course.get(course_key or course_name, 0) + minutes

    active_students_last_7d = len(active_user_ids)
    avg_minutes_per_active_student_last_7d = (
        float(total_study_minutes_last_7d) / active_students_last_7d if active_students_last_7d > 0 else 0.0
    )

    weekday_minutes = WeekdayMinutes(minutes_by_weekday=minutes_by_weekday)

    top_courses: list[TopCourseItem] = []
    for key, mins in minutes_by_course.items():
        if mins <= 0:
            continue
        label = key or "Unassigned"
        top_courses.append(
            TopCourseItem(
                course_id=key,
                course_name=label,
                minutes=mins,
            )
        )
    top_courses.sort(key=lambda item: item.minutes, reverse=True)
    if len(top_courses) > 5:
        top_courses = top_courses[:5]

    return InstitutionOverview(
        institution_id=inst.id,
        institution_name=inst.name,
        total_students=total_students,
        active_students_last_7d=active_students_last_7d,
        total_study_minutes_last_7d=total_study_minutes_last_7d,
        avg_minutes_per_active_student_last_7d=avg_minutes_per_active_student_last_7d,
        weekday_minutes=weekday_minutes,
        top_courses=top_courses,
    )
