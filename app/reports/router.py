from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.models import User
from app.reports.schemas import InstitutionReportData
from app.reports.service import build_institution_report_data
from app.reports.pdf import generate_institution_report_pdf
from app.reports.runner import run_institution_reports_for_period

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/institutions/{institution_id}/data", response_model=InstitutionReportData)
def get_institution_report_data(
    institution_id: UUID,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> InstitutionReportData:
    if not current_user.is_institution_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view institution reports",
        )
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view another institution's report",
        )

    return build_institution_report_data(
        db=db,
        institution_id=institution_id,
        days=days,
    )


@router.get("/institutions/{institution_id}/pdf")
def get_institution_report_pdf(
    institution_id: UUID,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    if not current_user.is_institution_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view institution reports",
        )
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view another institution's report",
        )

    data = build_institution_report_data(db, institution_id, days=days)
    pdf_bytes = generate_institution_report_pdf(data)
    filename = (
        f"teski-learning-climate-{data.summary.institution_name}-"
        f"{data.summary.period_start}-to-{data.summary.period_end}.pdf"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/internal/run-institution-reports")
def run_institution_reports_endpoint(
    background_tasks: BackgroundTasks,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not current_user.is_institution_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run institution reports",
        )

    def _job() -> None:
        session_gen = get_session()
        session = next(session_gen)
        try:
            run_institution_reports_for_period(session, days=days)
        finally:
            try:
                session_gen.close()
            except Exception:
                pass

    background_tasks.add_task(_job)
    return {"detail": "Report generation started in background"}
