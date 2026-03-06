from __future__ import annotations

from pydantic import BaseModel


class ExamResult(BaseModel):
    course_code: str
    course_name: str
    department: str
    date: str      # YYYY-MM-DD or empty string if unparseable
    pdf_url: str   # absolute URL ending in .pdf
    has_exams: bool = False
    exam_count: int = 0
    exam_pdf_urls: list[str] = []


class CourseSearchResponse(BaseModel):
    query: str
    results: list[ExamResult]
    total_found: int
