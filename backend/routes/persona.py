# >>> PERSONA START
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db import get_session
from ..services.persona import get_persona, list_personas
from ..services.nudges import generate_nudge, choose_bucket

router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


@router.get("/", response_model=dict)
def list_personas_endpoint(db: Session = Depends(get_session)):
    items = [{"code": persona.code, "displayName": persona.display_name} for persona in list_personas(db)]
    return {"items": items}


@router.get("/{code}", response_model=dict)
def read_persona(code: str, db: Session = Depends(get_session)):
    persona = get_persona(db, code)
    if not persona:
        raise HTTPException(status_code=404, detail="persona_not_found")
    return {"code": persona.code, "displayName": persona.display_name, "config": persona.config}


@router.post("/nudge/preview", response_model=dict)
def preview_nudge(payload: dict, db: Session = Depends(get_session)):
    """
    payload: {
      "requestedMood": "mood_snark_v1" | null,
      "phase": "preTask" | "duringTask" | "postTaskSuccess" | "postTaskFail",
      "context": {"taskId": 123, "minutesToDue": 180, "overdue": false, "repeatedDeferrals": 1}
    }
    """
    phase = payload.get("phase", "preTask")
    context = payload.get("context", {}) or {}
    mood_code = payload.get("requestedMood")
    if not mood_code:
        mood_code = choose_bucket(
            int(context.get("minutesToDue", 9999)),
            bool(context.get("overdue", False)),
            int(context.get("repeatedDeferrals", 0)),
        )
    persona = get_persona(db, mood_code)
    if not persona:
        raise HTTPException(status_code=404, detail="persona_not_found")
    return generate_nudge(persona.config, phase, context)
# <<< PERSONA END
