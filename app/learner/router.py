from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.models import User

from .models import LearnerProfile
from .service import get_learner_profile, get_or_default_profile

router = APIRouter(prefix="/onboarding", tags=["learner-onboarding"])

QUESTION_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "approach_new_topic",
        "type": "single_choice",
        "prompt": "How do you usually begin learning something new?",
        "options": [
            {"id": "skim_first", "label": "I skim everything first to get the big picture."},
            {"id": "examples_first", "label": "I look at examples or worked solutions before theory."},
            {"id": "slow_read", "label": "I read slowly and carefully from start to finish."},
            {"id": "videos_first", "label": "I search for a video or walkthrough before reading."},
        ],
    },
    {
        "id": "stuck_strategy",
        "type": "single_choice",
        "prompt": "What is your first move when you get stuck?",
        "options": [
            {"id": "reread", "label": "Reread the material until it clicks."},
            {"id": "search_online", "label": "Search online or watch another explanation."},
            {"id": "try_problems", "label": "Keep trying related problems until I figure it out."},
            {"id": "ask_help", "label": "Ask a friend/tutor/teacher for help."},
            {"id": "move_on", "label": "Move on and come back later with a fresh mind."},
        ],
    },
    {
        "id": "explanation_style",
        "type": "single_choice",
        "prompt": "Which explanation style lands best for you?",
        "options": [
            {"id": "step_by_step", "label": "Step-by-step logic and structure."},
            {"id": "big_picture", "label": "Big-picture overview before details."},
            {"id": "analogy", "label": "Analogies or stories that map to real life."},
            {"id": "visual", "label": "Visuals, diagrams, or animations."},
            {"id": "problems", "label": "Seeing several worked problems first."},
        ],
    },
    {
        "id": "confidence_baseline",
        "type": "single_choice",
        "prompt": "How confident do you usually feel before starting an assignment?",
        "options": [
            {"id": 1, "label": "1 - I rarely feel confident until I start working."},
            {"id": 2, "label": "2 - I need a bit of warm up before I feel ready."},
            {"id": 3, "label": "3 - I'm moderately confident most of the time."},
            {"id": 4, "label": "4 - I feel confident once I review the material."},
            {"id": 5, "label": "5 - I feel very confident jumping right in."},
        ],
    },
    {
        "id": "long_assignment_reaction",
        "type": "single_choice",
        "prompt": "When you see a long assignment, what is your gut reaction?",
        "options": [
            {"id": "motivated", "label": "Motivated — I start mapping out a plan immediately."},
            {"id": "stressful", "label": "Stressful — I know I'll need help managing it."},
            {"id": "overwhelmed", "label": "Overwhelmed — it takes effort to even begin."},
            {"id": "procrastinate", "label": "Procrastinate — I tend to delay until there's pressure."},
        ],
    },
    {
        "id": "focus_time",
        "type": "single_choice",
        "prompt": "When is your best focus window?",
        "options": [
            {"id": "morning", "label": "Early morning"},
            {"id": "afternoon", "label": "Mid-day / afternoon"},
            {"id": "evening", "label": "Evening"},
            {"id": "late_night", "label": "Late night"},
            {"id": "varies", "label": "It varies depending on the week."},
        ],
    },
    {
        "id": "communication_style",
        "type": "single_choice",
        "prompt": "What tone do you want from Teski when it sends nudges or explanations?",
        "options": [
            {"id": "short", "label": "Short and to the point."},
            {"id": "normal", "label": "Friendly and conversational."},
            {"id": "detailed", "label": "Detailed with full context."},
            {"id": "supportive", "label": "Supportive and encouraging."},
            {"id": "strict", "label": "Strict accountability style."},
        ],
    },
    {
        "id": "practice_style",
        "type": "single_choice",
        "prompt": "How do you prefer to practice?",
        "options": [
            {"id": "short_bursts", "label": "Short bursts spread across the day."},
            {"id": "long_sessions", "label": "Long, focused sessions."},
            {"id": "mixed", "label": "A mix of both."},
            {"id": "depends", "label": "Depends on the topic."},
        ],
    },
    {
        "id": "time_estimation_bias",
        "type": "single_choice",
        "prompt": "How well do you estimate how long work will take?",
        "options": [
            {"id": "underestimates_heavily", "label": "I dramatically underestimate time needed."},
            {"id": "underestimates_slightly", "label": "I slightly underestimate most tasks."},
            {"id": "accurate", "label": "I'm usually accurate."},
            {"id": "overestimates", "label": "I tend to overestimate and finish early."},
        ],
    },
    {
        "id": "analytical_comfort",
        "type": "single_choice",
        "prompt": "How comfortable are you with analytical or quantitative work?",
        "options": [
            {"id": 1, "label": "1 - I avoid it whenever possible."},
            {"id": 2, "label": "2 - I can handle it with guidance."},
            {"id": 3, "label": "3 - I'm fine with most analytical tasks."},
            {"id": 4, "label": "4 - I enjoy analytical work."},
            {"id": 5, "label": "5 - It's one of my strengths."},
        ],
    },
    {
        "id": "feedback_preference",
        "type": "single_choice",
        "prompt": "Which feedback style motivates you most?",
        "options": [
            {"id": "blunt", "label": "Blunt and direct."},
            {"id": "supportive", "label": "Supportive encouragement first."},
            {"id": "examples", "label": "Examples of what to fix."},
            {"id": "next_steps", "label": "Clear next steps."},
            {"id": "minimal", "label": "Minimal feedback unless it's critical."},
        ],
    },
    {
        "id": "challenges",
        "type": "multi_select",
        "prompt": "Which challenges should Teski watch out for? (Select all that apply)",
        "options": [
            {"id": "consistency", "label": "Staying consistent week to week."},
            {"id": "deep_understanding", "label": "Getting to deep understanding, not just memorizing."},
            {"id": "starting_tasks", "label": "Getting started on tasks."},
            {"id": "organizing", "label": "Organizing materials or plans."},
            {"id": "remembering", "label": "Remembering content later on."},
            {"id": "applying", "label": "Applying ideas to new problems."},
        ],
    },
    {
        "id": "primary_device",
        "type": "single_choice",
        "prompt": "What device do you primarily learn on?",
        "options": [
            {"id": "laptop", "label": "Laptop or desktop"},
            {"id": "tablet", "label": "Tablet"},
            {"id": "phone", "label": "Phone"},
            {"id": "mixed", "label": "A mix of devices"},
        ],
    },
    {
        "id": "proactivity_level",
        "type": "single_choice",
        "prompt": "How proactive are you about planning your study week?",
        "options": [
            {"id": "low", "label": "I react to whatever is urgent."},
            {"id": "medium", "label": "I plan occasionally but not consistently."},
            {"id": "high", "label": "I plan most weeks."},
            {"id": "very_high", "label": "I plan all major tasks proactively."},
        ],
    },
    {
        "id": "semester_goal",
        "type": "single_choice",
        "prompt": "What is your primary goal this semester?",
        "options": [
            {"id": "pass", "label": "Pass the course and stay afloat."},
            {"id": "improve_grades", "label": "Improve grades versus last term."},
            {"id": "master_subject", "label": "Master the subject deeply."},
            {"id": "prepare_advanced", "label": "Prepare for a more advanced class."},
            {"id": "reduce_stress", "label": "Reduce stress and feel more balanced."},
            {"id": "build_habits", "label": "Build strong study habits."},
        ],
    },
]

CHOICE_MAP: Dict[str, Set[Any]] = {
    question["id"]: {option["id"] for option in question.get("options", [])}
    for question in QUESTION_DEFINITIONS
}
MULTI_SELECT_FIELDS: Set[str] = {
    question["id"] for question in QUESTION_DEFINITIONS if question["type"] == "multi_select"
}


class LearnerProfileAnswers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approach_new_topic: str
    stuck_strategy: str
    explanation_style: str
    confidence_baseline: int = Field(ge=1, le=5)
    long_assignment_reaction: str
    focus_time: str
    communication_style: str
    practice_style: str
    time_estimation_bias: str
    analytical_comfort: int = Field(ge=1, le=5)
    feedback_preference: str
    challenges: List[str] = Field(min_length=1)
    primary_device: str
    proactivity_level: str
    semester_goal: str

    @model_validator(mode="after")
    def validate_choices(self) -> "LearnerProfileAnswers":
        for field_name, allowed in CHOICE_MAP.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue
            if field_name in MULTI_SELECT_FIELDS:
                invalid = [item for item in value if item not in allowed]
                if invalid:
                    raise ValueError(f"Invalid selections for {field_name}: {invalid}")
            else:
                if value not in allowed:
                    raise ValueError(f"Invalid value '{value}' for {field_name}")
        return self


class LearnerProfileSubmit(BaseModel):
    answers: LearnerProfileAnswers


def _serialize_profile(profile: LearnerProfile) -> Dict[str, Any]:
    data = profile.model_dump()
    data["challenges"] = data.get("challenges") or []
    return data
@router.get("/questions")
def get_questions() -> Dict[str, Any]:
    return {"version": "v1", "questions": QUESTION_DEFINITIONS}


@router.get("/profile")
def get_profile(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    profile = get_learner_profile(session, user.id)
    if profile is None:
        return {"exists": False}
    return {"exists": True, "profile": _serialize_profile(profile)}


@router.post("/submit")
def submit_profile(
    payload: LearnerProfileSubmit,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    profile = get_or_default_profile(session, user.id)
    data = payload.answers.model_dump()
    for field_name, value in data.items():
        setattr(profile, field_name, value)
    profile.user_id = user.id
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return {"status": "ok", "profile": _serialize_profile(profile)}
