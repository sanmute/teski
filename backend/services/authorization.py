from __future__ import annotations

from sqlmodel import Session, select

from backend.models import User, UserRole
from backend.models_institution import (
    Course,
    Institution,
    UserInstitutionRole,
    InstitutionRole,
    UserCourseRole,
    CourseRole,
)


def user_can_edit_course(user: User, course: Course, session: Session) -> bool:
    """Centralized course edit permission check."""
    if user.role == UserRole.TESKI_ADMIN:
        return True

    institution = session.get(Institution, course.institution_id)
    if not institution:
        return False

    inst_admin = session.exec(
        select(UserInstitutionRole).where(
            UserInstitutionRole.user_id == user.id,
            UserInstitutionRole.institution_id == institution.id,
            UserInstitutionRole.role == InstitutionRole.INSTITUTION_ADMIN,
        )
    ).first()
    if inst_admin:
        return True

    course_role = session.exec(
        select(UserCourseRole).where(
            UserCourseRole.user_id == user.id,
            UserCourseRole.course_id == course.id,
            UserCourseRole.role.in_([CourseRole.OWNER, CourseRole.EDITOR]),
        )
    ).first()
    return course_role is not None
