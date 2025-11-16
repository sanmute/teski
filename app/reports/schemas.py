from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class Trend(BaseModel):
    current: float
    previous: Optional[float] = None
    direction: TrendDirection


class ReportSummary(BaseModel):
    institution_id: UUID
    institution_name: str
    period_start: date
    period_end: date

    consenting_students: int
    active_students: int

    total_study_minutes: int
    avg_minutes_per_active_student: float

    total_minutes_trend: Optional[Trend] = None
    active_students_trend: Optional[Trend] = None


class WeekdayDistribution(BaseModel):
    minutes_by_weekday: Dict[int, int]


class CourseLoadItem(BaseModel):
    course_id: Optional[str]
    course_name: str
    minutes: int
    share_of_total: float


class CourseLoadSection(BaseModel):
    total_minutes: int
    top_courses: List[CourseLoadItem]


class InstitutionReportData(BaseModel):
    generated_at: datetime
    summary: ReportSummary
    workload: WeekdayDistribution
    course_load: CourseLoadSection
