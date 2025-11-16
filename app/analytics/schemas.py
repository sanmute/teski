from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class SummaryMetrics(BaseModel):
    today_minutes: int
    today_blocks: int
    week_minutes: int
    week_blocks: int
    streak_days: int


class DailyPoint(BaseModel):
    date: date
    minutes: int
    blocks: int


class DailySeries(BaseModel):
    days: List[DailyPoint]


class CourseBreakdownItem(BaseModel):
    course_id: Optional[str]
    course_name: str
    minutes: int
    blocks: int
    on_track: Optional[bool] = None


class CourseBreakdown(BaseModel):
    items: List[CourseBreakdownItem]


class InsightSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class InsightCategory(str, Enum):
    consistency = "consistency"
    balance = "balance"
    workload = "workload"
    timing = "timing"
    focus = "focus"


class Insight(BaseModel):
    id: str
    severity: InsightSeverity
    category: InsightCategory
    title: str
    message: str


class InsightList(BaseModel):
    insights: List[Insight]


class WeekdayMinutes(BaseModel):
    minutes_by_weekday: Dict[int, int]


class TopCourseItem(BaseModel):
    course_id: Optional[str]
    course_name: str
    minutes: int


class InstitutionOverview(BaseModel):
    institution_id: UUID
    institution_name: str
    total_students: int
    active_students_last_7d: int
    total_study_minutes_last_7d: int
    avg_minutes_per_active_student_last_7d: float
    weekday_minutes: WeekdayMinutes
    top_courses: List[TopCourseItem]
