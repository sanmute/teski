# >>> PERSONA START
import json
import sys

from sqlmodel import Session, SQLModel

from backend.db import get_engine
from backend.services.persona import upsert_persona


def main(path: str = "seed/personas.teski.json"):
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    with Session(engine) as db:
        for persona in payload["personas"]:
            upsert_persona(db, persona["code"], persona["displayName"], persona)
    print("Seeded personas:", [persona["code"] for persona in payload["personas"]])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "seed/personas.teski.json")
# <<< PERSONA END
