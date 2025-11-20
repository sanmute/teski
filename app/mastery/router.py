from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.mastery.schemas import SkillMasteryOut
from app.mastery.service import get_masteries_for_user, get_mastery_for_skill
from app.models import User

router = APIRouter(prefix="/mastery", tags=["mastery"])


@router.get("", response_model=list[SkillMasteryOut])
def list_mastery(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SkillMasteryOut]:
    data = get_masteries_for_user(db, current_user.id)
    return [SkillMasteryOut(**item) for item in data]


@router.get("/{skill_id}", response_model=SkillMasteryOut)
def get_mastery_detail(
    skill_id: UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SkillMasteryOut:
    data = get_mastery_for_skill(db, current_user.id, skill_id)
    return SkillMasteryOut(**data)
