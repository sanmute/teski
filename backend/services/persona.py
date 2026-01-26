# >>> PERSONA START
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from models import Persona


def upsert_persona(db: Session, code: str, display_name: str, config: Dict[str, Any]) -> Persona:
    persona = db.exec(select(Persona).where(Persona.code == code)).first()
    if persona:
        persona.display_name = display_name
        persona.config = config
    else:
        persona = Persona(code=code, display_name=display_name, config=config)
        db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def get_persona(db: Session, code: str) -> Optional[Persona]:
    return db.exec(select(Persona).where(Persona.code == code)).first()


def list_personas(db: Session) -> List[Persona]:
    return list(db.exec(select(Persona)).all())
# <<< PERSONA END
