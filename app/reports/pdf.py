from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.reports.schemas import InstitutionReportData

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_institution_report_html(data: InstitutionReportData) -> str:
    template = _env.get_template("institution_report.html")
    html = template.render(
        summary=data.summary,
        workload=data.workload,
        course_load=data.course_load,
        generated_at=data.generated_at,
    )
    return html


def generate_institution_report_pdf(data: InstitutionReportData) -> bytes:
    html_str = render_institution_report_html(data)
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes
