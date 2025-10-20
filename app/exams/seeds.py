from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.exams.models import Exam, ExamTopic


def seed_example_exam(session: Session, user_id: UUID) -> UUID:
    """Create a small example exam with topics for demo purposes."""
    now = datetime.utcnow()
    exam_at = now + timedelta(days=10)

    existing = session.exec(
        select(Exam).where(Exam.user_id == user_id, Exam.title == "Basics of EE — Midterm")
    ).first()
    if existing:
        return existing.id

    exam = Exam(
        user_id=user_id,
        title="Basics of EE — Midterm",
        course="Basics of Electrical Engineering",
        exam_at=exam_at,
        target_grade=None,
        notes="Auto-seeded example exam.",
    )
    session.add(exam)
    session.flush()

    topics: Sequence[tuple[str, int, int, Sequence[str]]] = [
        ("KCL", 120, 3, []),
        ("KVL", 120, 2, ["KCL"]),
        ("Ohm", 90, 2, []),
        ("Thevenin", 90, 2, ["Ohm"]),
        ("RC basics", 120, 2, []),
    ]

    for name, minutes, priority, deps in topics:
        session.add(
            ExamTopic(
                exam_id=exam.id,
                name=name,
                est_minutes=minutes,
                priority=priority,
                dependencies=list(deps),
            )
        )
    session.commit()
    return exam.id
