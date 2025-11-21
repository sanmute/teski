from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from sqlmodel import Session

from app.analytics.schemas import (
    CourseBreakdown,
    DailySeries,
    InsightList,
    InstitutionOverview,
    SummaryMetrics,
)
from app.analytics.service import (
    compute_course_breakdown_for_user,
    compute_daily_series_for_user,
    compute_institution_overview,
    compute_summary_for_user,
    generate_insights_for_user,
)
from app.learning_trajectory_service import get_skill_trajectory, summarize_recent_trends
from app.db import get_session
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/analytics/me", tags=["analytics"])
institution_router = APIRouter(prefix="/analytics/institution", tags=["institution-analytics"])


@router.get("/summary", response_model=SummaryMetrics)
def get_my_summary(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SummaryMetrics:
    return compute_summary_for_user(db, current_user.id)


@router.get("/daily", response_model=DailySeries)
def get_my_daily(
    days: int = Query(14, ge=1, le=60),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DailySeries:
    return compute_daily_series_for_user(db, current_user.id, days=days)


@router.get("/by-course", response_model=CourseBreakdown)
def get_my_course_breakdown(
    days: int = Query(7, ge=1, le=60),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CourseBreakdown:
    return compute_course_breakdown_for_user(db, current_user.id, days=days)


@router.get("/insights", response_model=InsightList)
def get_my_insights(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> InsightList:
    return generate_insights_for_user(db, current_user.id)


@router.get("/skill-trajectory")
def analytics_skill_trajectory(
    skill_id: str,
    days_back: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    snapshots = get_skill_trajectory(db, current_user.id, UUID(skill_id), days_back=days_back)
    return {
        "skill_id": skill_id,
        "snapshots": [
            {
                "date": snap.date.isoformat(),
                "mastery_level": snap.mastery_level,
                "delta_since_prev": snap.delta_since_prev,
                "num_correct": snap.num_correct,
                "num_attempts": snap.num_attempts,
                "dominant_mistake_subtypes": snap.dominant_mistake_subtypes,
            }
            for snap in snapshots
        ],
    }


@router.get("/recent-trends")
def analytics_recent_trends(
    days_back: int = Query(7, ge=1, le=60),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return summarize_recent_trends(db, current_user.id, days_back=days_back)


@institution_router.get("/overview", response_model=InstitutionOverview)
def get_institution_overview(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> InstitutionOverview:
    if not current_user.is_institution_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for institution analytics",
        )
    if current_user.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to any institution",
        )

    return compute_institution_overview(db, current_user.institution_id)
