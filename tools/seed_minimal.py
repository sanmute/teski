from __future__ import annotations

import json
from textwrap import dedent
from uuid import UUID

from sqlmodel import Session

from app.config import get_settings
from app.db import engine, init_db
from app.exercises import Exercise, load_exercises
from app.models import User
from app.scheduler import schedule_from_mistake

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def ensure_demo_user(session: Session) -> User:
    user = session.get(User, DEMO_USER_ID)
    if user is None:
        settings = get_settings()
        user = User(
            id=DEMO_USER_ID,
            display_name="Demo Student",
            timezone="Europe/Helsinki",
            persona=settings.PERSONA_DEFAULT,
        )
        session.add(user)
        session.flush()
    return user


def ensure_sample_memory(session: Session, user: User) -> Exercise:
    exercises = load_exercises()
    if not exercises:
        raise RuntimeError("No exercises found in content/.")

    sample = exercises[0]
    schedule_from_mistake(session, user=user, concept=sample.concept)
    return sample


def build_payload(exercise: Exercise) -> str:
    if exercise.type == "numeric":
        answer = exercise.meta.get("answer", {})
        payload: dict[str, object] = {"value": answer.get("value")}
        unit = answer.get("unit")
        if unit:
            payload["unit"] = unit
        return json.dumps(payload)
    if exercise.type == "mcq":
        choices = exercise.meta.get("choices") or []
        correct = next((idx for idx, choice in enumerate(choices) if choice.get("correct")), 0)
        return json.dumps({"choice": correct})
    rubric = exercise.meta.get("rubric") or {}
    must_include = rubric.get("must_include") or []
    sample_text = " ".join(str(token) for token in must_include) or "Example answer"
    return json.dumps({"text": sample_text})


def main() -> int:
    init_db()
    with Session(engine) as session:
        user = ensure_demo_user(session)
        sample_exercise = ensure_sample_memory(session, user)
        session.commit()

    payload_json = build_payload(sample_exercise)
    curl_block = dedent(
        f"""
        curl -s 'http://localhost:8000/ex/list?page=1&page_size=5' | jq .
        curl -s 'http://localhost:8000/ex/get?id={sample_exercise.id}&user_id={DEMO_USER_ID}' | jq .
        curl -s -X POST 'http://localhost:8000/ex/submit?id={sample_exercise.id}&user_id={DEMO_USER_ID}' \\
            -H 'Content-Type: application/json' \\
            -d '{payload_json}' | jq .
        curl -s 'http://localhost:8000/memory/next?user_id={DEMO_USER_ID}' | jq .
        """
    ).strip()

    print("Seeded demo user:", DEMO_USER_ID)
    print("Sample exercise:", sample_exercise.id)
    print("\nTry the API with:\n")
    print(curl_block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
