from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.institutions.models import Institution
from app.models import User


def get_or_create_institution_by_domain(db: Session, domain: str, name: Optional[str] = None) -> Institution:
    stmt = select(Institution).where(Institution.domain == domain)
    inst = db.exec(stmt).first()
    if inst:
        return inst

    inst = Institution(
        name=name or domain,
        domain=domain,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def assign_user_institution_from_email(db: Session, user: User) -> None:
    if getattr(user, "institution_id", None) is not None:
        return

    email = getattr(user, "email", None) or ""
    if "@" not in email:
        return

    domain = email.split("@", 1)[1].lower().strip()
    if not domain:
        return

    inst = get_or_create_institution_by_domain(db, domain)
    user.institution_id = inst.id
    db.add(user)
    db.commit()
    db.refresh(user)
