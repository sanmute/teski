from __future__ import annotations

from pydantic import BaseModel


class ExamResult(BaseModel):
    course_code: str
    course_name: str
    department: str
    date: str      # YYYY-MM-DD or empty string if unparseable
    pdf_url: str   # absolute URL ending in .pdf


class CourseSearchResponse(BaseModel):
    query: str
    results: list[ExamResult]
    total_found: int
