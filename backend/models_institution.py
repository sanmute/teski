from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class InstitutionType(str, Enum):
    UNIVERSITY = "university"
    TRAINING_ORG = "training_org"
    OTHER = "other"


class Institution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True, sa_column_kwargs={"unique": True})
    type: InstitutionType = Field(default=InstitutionType.UNIVERSITY)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    courses: List["Course"] = Relationship(back_populates="institution")


class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    institution_id: int = Field(foreign_key="institution.id", index=True)
    code: Optional[str] = Field(default=None, index=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    institution: Institution = Relationship(back_populates="courses")
    modules: List["Module"] = Relationship(back_populates="course")


class Module(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    title: str
    order_index: int = Field(default=0, index=True)

    course: Course = Relationship(back_populates="modules")


class InstitutionRole(str, Enum):
    EDUCATOR = "educator"
    INSTITUTION_ADMIN = "institution_admin"


class UserInstitutionRole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    institution_id: int = Field(foreign_key="institution.id", index=True)
    role: InstitutionRole = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CourseRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class UserCourseRole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    role: CourseRole = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
