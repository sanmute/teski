from fastapi import APIRouter, Query
from services.topic_matcher import match_topics, merge_resources, merge_practice_prompts

router = APIRouter(prefix="/api/topics", tags=["topics"])

@router.get("/suggest")
def suggest_topics(title: str = Query(...), notes: str = ""):
    ranked = match_topics(title, notes)
    topics = [dict(topic=t, score=s) for t, s in ranked]
    resources = merge_resources([t for t, _ in ranked], limit=3)
    practice = merge_practice_prompts([t for t, _ in ranked], limit=1)
    return {"topics": topics, "resources": resources, "practice": practice}
