from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.learner.service import get_or_default_profile

from .schemas import ExplanationRequest, ExplanationResponse
from .service import generate_personalized_explanation

router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.post("/generate", response_model=ExplanationResponse)
async def generate_explanation(
    payload: ExplanationRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> ExplanationResponse:
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text_required")
    profile = get_or_default_profile(session, user.id)
    return await generate_personalized_explanation(text, profile, payload.mode)
