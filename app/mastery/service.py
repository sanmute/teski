from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.mastery.models import Skill, UserSkillMastery
from app.models import User
from app.timeutil import _utcnow


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return base or "skill"


def get_or_create_skill(session: Session, name: str) -> Skill:
    clean_name = name.strip()
    slug = _slugify(clean_name)
    skill = session.exec(select(Skill).where(Skill.slug == slug)).first()
    if skill:
        return skill
    skill = Skill(name=clean_name, slug=slug)
    session.add(skill)
    session.flush()
    session.refresh(skill)
    return skill


def get_mastery_record(session: Session, user_id: UUID, skill_id: UUID) -> UserSkillMastery:
    mastery = session.exec(
        select(UserSkillMastery).where(
            UserSkillMastery.user_id == user_id,
            UserSkillMastery.skill_id == skill_id,
        )
    ).first()
    if mastery:
        return mastery
    mastery = UserSkillMastery(user_id=user_id, skill_id=skill_id, mastery=0.0)
    session.add(mastery)
    session.flush()
    session.refresh(mastery)
    return mastery


def update_mastery(
    session: Session,
    user_id: UUID,
    skill_id: UUID,
    *,
    is_correct: bool,
    difficulty: int,
    mistake_type: str | None = None,
) -> Tuple[float, float]:
    record = get_mastery_record(session, user_id, skill_id)
    old_value = record.mastery
    subtype = (mistake_type or "other").split(":", 1)[-1]
    family = (mistake_type or "other").split(":", 1)[0]
    if is_correct:
        delta = 2 + (0.5 * difficulty)
    else:
        penalty = 1 + (0.3 * difficulty)
        if subtype in {"near_miss", "rounding", "rounding_or_precision_error", "rounding_error", "small_precision_error"}:
            penalty *= 0.5
        elif family == "units" and subtype in {"wrong_unit", "missing_unit", "conversion_error"}:
            penalty *= 0.7
        delta = -penalty

    new_value = max(0.0, min(100.0, old_value + delta))
    record.mastery = new_value
    record.updated_at = _utcnow()
    session.add(record)
    return old_value, new_value


def get_masteries_for_user(session: Session, user_id: UUID) -> list[dict]:
    results = session.exec(
        select(UserSkillMastery, Skill)
        .where(UserSkillMastery.user_id == user_id)
        .join(Skill, Skill.id == UserSkillMastery.skill_id)
    ).all()
    mastery_list: list[dict] = []
    for mastery, skill in results:
        mastery_list.append(
            {
                "skill_id": str(skill.id),
                "skill_name": skill.name,
                "mastery": mastery.mastery,
                "updated_at": mastery.updated_at,
            }
        )
    return mastery_list


def get_mastery_for_skill(session: Session, user_id: UUID, skill_id: UUID) -> dict:
    mastery = session.exec(
        select(UserSkillMastery)
        .where(UserSkillMastery.user_id == user_id, UserSkillMastery.skill_id == skill_id)
    ).first()
    skill = session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="skill_not_found")
    if mastery is None:
        return {
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "mastery": 0.0,
            "updated_at": None,
        }
    return {
        "skill_id": str(skill.id),
        "skill_name": skill.name,
        "mastery": mastery.mastery,
        "updated_at": mastery.updated_at,
    }


def ensure_skills(session: Session, names: Sequence[str]) -> list[Skill]:
    skills: list[Skill] = []
    seen: set[str] = set()
    for name in names:
        clean = name.strip()
        if not clean:
            continue
        slug = _slugify(clean)
        if slug in seen:
            continue
        seen.add(slug)
        skills.append(get_or_create_skill(session, clean))
    return skills


def mastery_snapshot_for_skills(
    session: Session,
    user_id: UUID,
    skills: Sequence[Skill],
) -> list[dict]:
    snapshots: list[dict] = []
    if not skills:
        return snapshots
    mastery_rows = session.exec(
        select(UserSkillMastery).where(
            UserSkillMastery.user_id == user_id,
            UserSkillMastery.skill_id.in_([skill.id for skill in skills]),
        )
    ).all()
    mastery_map = {row.skill_id: row.mastery for row in mastery_rows}
    for skill in skills:
        snapshots.append(
            {
                "skill_id": str(skill.id),
                "skill_name": skill.name,
                "mastery": mastery_map.get(skill.id, 0.0),
            }
        )
    return snapshots
