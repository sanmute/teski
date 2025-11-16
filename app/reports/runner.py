from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.core.email import send_email_with_attachment
from app.institutions.models import Institution
from app.reports.pdf import generate_institution_report_pdf
from app.reports.service import build_institution_report_data


def run_institution_reports_for_period(
    db: Session,
    days: int = 30,
    min_bucket_size: int = 10,
) -> int:
    institutions = db.exec(select(Institution)).all()
    sent_count = 0

    for inst in institutions:
        recipients = inst.report_recipients or []
        if not recipients:
            continue

        try:
            data = build_institution_report_data(
                db=db,
                institution_id=inst.id,
                days=days,
                min_bucket_size=min_bucket_size,
            )
        except Exception:
            continue

        pdf_bytes = generate_institution_report_pdf(data)
        filename = (
            f"teski-learning-climate-{data.summary.institution_name}-"
            f"{data.summary.period_start}-to-{data.summary.period_end}.pdf"
        )
        subject = f"Teski Learning Climate Report – {data.summary.institution_name}"
        body = (
            f"Attached is the Teski learning climate report for {data.summary.institution_name} "
            f"covering {data.summary.period_start} to {data.summary.period_end}.\n\n"
            "The report is based on anonymous, aggregated study sessions from students who opted in "
            "to learning analytics in Teski. No individual-level data is included."
        )

        send_email_with_attachment(
            to_addresses=recipients,
            subject=subject,
            body_text=body,
            filename=filename,
            pdf_bytes=pdf_bytes,
        )
        sent_count += 1

    return sent_count
