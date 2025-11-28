from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select
from datetime import datetime

from ..db import get_session
from ..models import User, UserRole
from ..models_institution import (
    Course,
    CourseRole,
    Institution,
    InstitutionRole,
    UserCourseRole,
    UserInstitutionRole,
)
from .deps import require_educator

router = APIRouter(prefix="/educator", tags=["educator"])


class EducatorInstitutionRead(SQLModel):
    institution_id: int
    name: str
    slug: str
    roles: List[str]


class EducatorCourseRead(SQLModel):
    id: int
    institution_id: int
    code: str | None
    name: str
    description: str | None
    created_at: datetime


class CourseCreate(SQLModel):
    code: Optional[str] = None
    name: str
    description: Optional[str] = None


class CourseRead(SQLModel):
    id: int
    institution_id: int
    code: Optional[str]
    name: str
    description: Optional[str] = None
    created_at: datetime


@router.get("/institutions", response_model=List[EducatorInstitutionRead])
def list_my_institutions(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_educator),
):
    rows = session.exec(
        select(UserInstitutionRole, Institution)
        .join(Institution, Institution.id == UserInstitutionRole.institution_id)
        .where(UserInstitutionRole.user_id == current_user.id)
    ).all()

    grouped: Dict[int, EducatorInstitutionRead] = {}
    for uir, inst in rows:
        if inst.id not in grouped:
            grouped[inst.id] = EducatorInstitutionRead(
                institution_id=inst.id,
                name=inst.name,
                slug=inst.slug,
                roles=[],
            )
        grouped[inst.id].roles.append(uir.role.value)
    return list(grouped.values())


@router.get("/institutions/{institution_id}/courses", response_model=List[EducatorCourseRead])
def list_courses_for_institution(
    institution_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_educator),
):
    uir = session.exec(
        select(UserInstitutionRole).where(
            UserInstitutionRole.user_id == current_user.id,
            UserInstitutionRole.institution_id == institution_id,
        )
    ).first()
    if not uir:
        raise HTTPException(
            status_code=403,
            detail="No educator access to this institution",
        )

    courses = session.exec(select(Course).where(Course.institution_id == institution_id)).all()
    return [
        EducatorCourseRead(
            id=c.id,
            institution_id=c.institution_id,
            code=c.code,
            name=c.name,
            description=c.description,
            created_at=c.created_at,
        )
        for c in courses
    ]


@router.post(
    "/institutions/{institution_id}/courses",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_course_for_institution(
    institution_id: int,
    payload: CourseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_educator),
):
    inst = session.exec(select(Institution).where(Institution.id == institution_id)).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    if current_user.role == UserRole.TESKI_ADMIN:
        allowed = True
    else:
        uir = session.exec(
            select(UserInstitutionRole).where(
                UserInstitutionRole.user_id == current_user.id,
                UserInstitutionRole.institution_id == institution_id,
                UserInstitutionRole.role == InstitutionRole.INSTITUTION_ADMIN,
            )
        ).first()
        allowed = uir is not None

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to create courses for this institution",
        )

    if payload.code:
        existing_course = session.exec(
            select(Course).where(
                Course.institution_id == institution_id,
                Course.code == payload.code,
            )
        ).first()
        if existing_course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course code already exists for this institution",
            )

    new_course = Course(
        institution_id=institution_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
    )
    session.add(new_course)
    session.commit()
    session.refresh(new_course)
    creator_owner_role = UserCourseRole(
        user_id=current_user.id,
        course_id=new_course.id,
        role=CourseRole.OWNER,
    )
    session.add(creator_owner_role)
    session.commit()
    return CourseRead(
        id=new_course.id,
        institution_id=new_course.institution_id,
        code=new_course.code,
        name=new_course.name,
        description=new_course.description,
        created_at=new_course.created_at,
    )

# Future course-scoped endpoints (e.g., module/exercise management) should depend on require_course_editor
# to centralize edit permissions at the course level.
