# >>> LEADERBOARD START SERVICE
"""Service layer for leaderboard operations."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.core.leaderboard_constants import (
    DEFAULT_EVENT_POINTS,
    DEFAULT_TZ,
)
from backend.models import User
from backend.models_leaderboard import (
    Leaderboard,
    LeaderboardMember,
    PointsEvent,
    WeeklyScore,
)
from backend.schemas_leaderboard import LeaderboardOut, MemberOut, LeaderboardStandings
from backend.utils.codes import generate_join_code
from backend.utils.crypto import anon_handle
from backend.utils.time import now_utc, to_week_key, start_end_of_week_iso
from backend.services.memory_bridge import record_xp_event


# >>> LEADERBOARD START UTIL
def _scalar(first_value):
    if first_value is None:
        return None
    if isinstance(first_value, (tuple, list)):
        return first_value[0] if first_value else None
    return first_value
# >>> LEADERBOARD END UTIL


def _ensure_join_code(db: Session) -> str:
    for _ in range(5):
        code = generate_join_code()
        if not db.exec(select(Leaderboard).where(Leaderboard.join_code == code)).first():
            return code
    raise HTTPException(status_code=500, detail="Could not allocate unique join code")


def _fetch_leaderboard(db: Session, leaderboard_id: int) -> Leaderboard:
    board = db.get(Leaderboard, leaderboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leaderboard not found")
    return board


def create_leaderboard(db: Session, *, name: str, course_id: Optional[str], creator: User) -> Leaderboard:
    code = _ensure_join_code(db).upper()
    board = Leaderboard(name=name, course_id=course_id, join_code=code, creator_user_id=creator.id)
    db.add(board)
    db.flush()
    member = LeaderboardMember(leaderboard_id=board.id, user_id=creator.id, display_consent=bool(creator.display_name))
    db.add(member)
    db.commit()
    db.refresh(board)
    return board


def join_leaderboard(db: Session, *, leaderboard_code: str, user: User) -> LeaderboardMember:
    normalized = leaderboard_code.upper()
    board = db.exec(select(Leaderboard).where(Leaderboard.join_code == normalized)).first()
    if not board:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid join code")
    existing = db.exec(
        select(LeaderboardMember).where(
            LeaderboardMember.leaderboard_id == board.id,
            LeaderboardMember.user_id == user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined")
    membership = LeaderboardMember(leaderboard_id=board.id, user_id=user.id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def _weekly_score(db: Session, leaderboard_id: int, user_id: int, week: Tuple[int, int]) -> WeeklyScore:
    week_year, week_number = week
    score = db.exec(
        select(WeeklyScore).where(
            WeeklyScore.leaderboard_id == leaderboard_id,
            WeeklyScore.user_id == user_id,
            WeeklyScore.week_year == week_year,
            WeeklyScore.week_number == week_number,
        )
    ).first()
    if score:
        return score
    score = WeeklyScore(
        leaderboard_id=leaderboard_id,
        user_id=user_id,
        week_year=week_year,
        week_number=week_number,
        points=0,
    )
    db.add(score)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        score = db.exec(
            select(WeeklyScore).where(
                WeeklyScore.leaderboard_id == leaderboard_id,
                WeeklyScore.user_id == user_id,
                WeeklyScore.week_year == week_year,
                WeeklyScore.week_number == week_number,
            )
        ).first()
        if not score:
            raise HTTPException(status_code=500, detail="Unable to upsert weekly score")
    return score


def _ensure_member(db: Session, leaderboard_id: int, user_id: int) -> LeaderboardMember:
    membership = db.exec(
        select(LeaderboardMember).where(
            LeaderboardMember.leaderboard_id == leaderboard_id,
            LeaderboardMember.user_id == user_id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not joined")
    return membership


def award_points(
    db: Session,
    *,
    leaderboard_id: int,
    user_id: int,
    event_type: str,
    points: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> PointsEvent:
    board = _fetch_leaderboard(db, leaderboard_id)
    _ensure_member(db, board.id, user_id)

    if points is None:
        if event_type not in DEFAULT_EVENT_POINTS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown event_type")
        points_value = DEFAULT_EVENT_POINTS[event_type]
    else:
        points_value = points

    week = to_week_key(now_utc())
    score = _weekly_score(db, leaderboard_id, user_id, week)
    score.points += points_value

    event = PointsEvent(
        leaderboard_id=leaderboard_id,
        user_id=user_id,
        event_type=event_type,
        points=points_value,
        meta=meta,
    )
    db.add(event)
    db.add(score)
    db.commit()
    db.refresh(event)

    try:
        record_xp_event(db, user_id=user_id, amount=points_value, reason=event_type)
    except Exception:
        pass

    return event


def _week_info_from_key(week: Tuple[int, int], tz: str) -> Dict[str, Any]:
    year, number = week
    try:
        start, end = start_end_of_week_iso(year, number, tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone") from exc
    return {
        "year": year,
        "number": number,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


def _streak_days(db: Session, leaderboard_id: int, user_id: int, tz: str) -> int:
    tzinfo = ZoneInfo(tz)
    now = now_utc()
    window_start = now - timedelta(days=14)
    events = db.exec(
        select(PointsEvent).where(
            PointsEvent.leaderboard_id == leaderboard_id,
            PointsEvent.user_id == user_id,
            PointsEvent.occurred_at >= window_start,
        )
    ).all()
    totals: Dict[date, int] = defaultdict(int)
    for event in events:
        local_date = event.occurred_at.astimezone(tzinfo).date()
        totals[local_date] += event.points
    streak = 0
    cursor = now.astimezone(tzinfo).date()
    while totals.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _member_summary(
    db: Session,
    board: Leaderboard,
    member: LeaderboardMember,
    tz: str,
    week: Tuple[int, int],
) -> MemberOut:
    user = db.get(User, member.user_id)
    if not user:
        raise HTTPException(status_code=500, detail="User missing")

    year, number = week
    weekly_points_row = db.exec(
        select(WeeklyScore.points).where(
            WeeklyScore.leaderboard_id == board.id,
            WeeklyScore.user_id == member.user_id,
            WeeklyScore.week_year == year,
            WeeklyScore.week_number == number,
        )
    ).first()
    weekly_points_value = _scalar(weekly_points_row)
    weekly_points = int(weekly_points_value or 0)

    total_points_row = db.exec(
        select(func.coalesce(func.sum(PointsEvent.points), 0)).where(
            PointsEvent.leaderboard_id == board.id,
            PointsEvent.user_id == member.user_id,
        )
    ).first()
    lifetime_value = _scalar(total_points_row)
    lifetime = int(lifetime_value or 0)

    handle = anon_handle(user.id, user.email)
    display_name = user.display_name if member.display_consent and user.display_name else None
    streak = _streak_days(db, board.id, member.user_id, tz)

    return MemberOut(
        user_id=user.id,
        display_name=display_name,
        anon_handle=handle,
        display_consent=member.display_consent,
        weekly_points=weekly_points,
        total_points=lifetime,
        streak_days=streak,
    )


def get_standings(db: Session, *, leaderboard_id: int, tz: str = DEFAULT_TZ) -> LeaderboardStandings:
    board = _fetch_leaderboard(db, leaderboard_id)
    members = db.exec(
        select(LeaderboardMember).where(LeaderboardMember.leaderboard_id == board.id)
    ).all()

    week_key = to_week_key(now_utc())
    week_info = _week_info_from_key(week_key, tz)
    summary_pairs = [(_member_summary(db, board, member, tz, week_key), member.joined_at) for member in members]
    summary_pairs.sort(
        key=lambda item: (-item[0].weekly_points, -item[0].total_points, item[1])
    )
    summaries = [item[0] for item in summary_pairs]

    leaderboard_out = LeaderboardOut.model_validate(board)
    return LeaderboardStandings(leaderboard=leaderboard_out, week=week_info, members=summaries)


def set_member_consent(
    db: Session,
    *,
    leaderboard_id: int,
    user_id: int,
    display_consent: bool,
    tz: str = DEFAULT_TZ,
) -> MemberOut:
    board = _fetch_leaderboard(db, leaderboard_id)
    member = _ensure_member(db, leaderboard_id, user_id)
    member.display_consent = display_consent
    db.add(member)
    db.commit()
    db.refresh(member)
    week_key = to_week_key(now_utc())
    return _member_summary(db, board, member, tz, week_key)


def force_new_week(db: Session, *, leaderboard_id: int, tz: str = DEFAULT_TZ) -> Dict[str, Any]:
    board = _fetch_leaderboard(db, leaderboard_id)
    now = now_utc()
    year, number = to_week_key(now)
    try:
        start, end = start_end_of_week_iso(year, number, tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone") from exc
    next_start = end
    next_end = end + timedelta(days=7)
    return {
        "leaderboard_id": board.id,
        "current_week": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "year": year,
            "number": number,
        },
        "next_week": {
            "start": next_start.isoformat(),
            "end": next_end.isoformat(),
        },
        "note": "Weekly reset is logical; no persisted changes performed.",
    }
# >>> LEADERBOARD END SERVICE
