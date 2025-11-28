from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Session, select

from ..db import get_session
from ..models import User
from ..models_institution import Institution, InstitutionType
from .deps import require_teski_admin

router = APIRouter(prefix="/admin/institutions", tags=["institutions-admin"])


class InstitutionCreate(SQLModel):
    name: str
    slug: str
    type: InstitutionType = InstitutionType.UNIVERSITY


class InstitutionRead(SQLModel):
    id: int
    name: str
    slug: str
    type: InstitutionType


@router.post("/", response_model=InstitutionRead)
def create_institution(
    payload: InstitutionCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_teski_admin),
):
    existing = session.exec(select(Institution).where(Institution.slug == payload.slug)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution slug already exists")

    inst = Institution(
        name=payload.name,
        slug=payload.slug,
        type=payload.type,
    )
    session.add(inst)
    session.commit()
    session.refresh(inst)
    return inst


@router.get("/", response_model=List[InstitutionRead])
def list_institutions(
    session: Session = Depends(get_session),
    _: User = Depends(require_teski_admin),
):
    return session.exec(select(Institution)).all()
