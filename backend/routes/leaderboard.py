# >>> LEADERBOARD START ROUTER
"""API routes for leaderboards."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from backend.core.leaderboard_constants import DEFAULT_TZ
from backend.db import get_session
from backend.models import User
from backend.models_leaderboard import Leaderboard, LeaderboardMember
from backend.routes.deps import get_current_user
from backend.schemas_leaderboard import (
    AwardPoints,
    JoinLeaderboard,
    LeaderboardCreate,
    LeaderboardOut,
    LeaderboardStandings,
    MemberConsent,
    MemberOut,
    PointsEventOut,
)
from backend.services import leaderboard as leaderboard_service

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])


@router.post("/", response_model=LeaderboardOut, status_code=status.HTTP_201_CREATED)
async def create_leaderboard_endpoint(
    payload: LeaderboardCreate,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    board = leaderboard_service.create_leaderboard(db, name=payload.name, course_id=payload.course_id, creator=user)
    return board


@router.post("/join", response_model=LeaderboardOut)
async def join_leaderboard_endpoint(
    payload: JoinLeaderboard,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    membership = leaderboard_service.join_leaderboard(db, leaderboard_code=payload.code, user=user)
    board = db.get(Leaderboard, membership.leaderboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leaderboard not found")
    return board


@router.get("/{leaderboard_id}", response_model=LeaderboardStandings)
async def get_leaderboard_standings(
    leaderboard_id: int,
    tz: str | None = Query(default=None, description="IANA timezone for week window"),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    board = db.get(Leaderboard, leaderboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leaderboard not found")
    membership = db.exec(
        select(LeaderboardMember).where(
            LeaderboardMember.leaderboard_id == leaderboard_id,
            LeaderboardMember.user_id == user.id,
        )
    ).first()
    if not membership and board.creator_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    tz_value = tz or DEFAULT_TZ
    return leaderboard_service.get_standings(db, leaderboard_id=leaderboard_id, tz=tz_value)


@router.post("/{leaderboard_id}/award", response_model=PointsEventOut, status_code=status.HTTP_201_CREATED)
async def award_points_endpoint(
    leaderboard_id: int,
    payload: AwardPoints,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    board = db.get(Leaderboard, leaderboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leaderboard not found")
    actor_membership = db.exec(
        select(LeaderboardMember).where(
            LeaderboardMember.leaderboard_id == leaderboard_id,
            LeaderboardMember.user_id == user.id,
        )
    ).first()
    if not actor_membership and board.creator_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")

    target_user_id = user_id or user.id
    if target_user_id != user.id and board.creator_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot award other members")

    event = leaderboard_service.award_points(
        db,
        leaderboard_id=leaderboard_id,
        user_id=target_user_id,
        event_type=payload.event_type,
        points=payload.points,
        meta=payload.meta,
    )
    return event


@router.post("/{leaderboard_id}/consent", response_model=MemberOut)
async def set_member_consent_endpoint(
    leaderboard_id: int,
    payload: MemberConsent,
    tz: str | None = Query(default=None),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    membership = db.exec(
        select(LeaderboardMember).where(
            LeaderboardMember.leaderboard_id == leaderboard_id,
            LeaderboardMember.user_id == user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    tz_value = tz or DEFAULT_TZ
    return leaderboard_service.set_member_consent(
        db,
        leaderboard_id=leaderboard_id,
        user_id=user.id,
        display_consent=payload.display_consent,
        tz=tz_value,
    )


@router.post("/{leaderboard_id}/admin/force-week")
async def force_week_endpoint(
    leaderboard_id: int,
    tz: str | None = Query(default=None),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    board = db.get(Leaderboard, leaderboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leaderboard not found")
    if board.creator_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires leaderboard creator")
    tz_value = tz or DEFAULT_TZ
    return leaderboard_service.force_new_week(db, leaderboard_id=leaderboard_id, tz=tz_value)
# >>> LEADERBOARD END ROUTER
