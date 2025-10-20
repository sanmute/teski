from __future__ import annotations

from typing import Dict, List

from app.exams.schemas import QuestionnaireIn, QuestionnaireOut

STYLES = [
    "spaced_structured",
    "cram_then_revise",
    "interleaved_hands_on",
    "theory_first",
]

QUESTION_BANK: List[Dict[str, object]] = [
    {
        "key": "time_availability",
        "prompt": "How much time can you dedicate daily to study?",
        "weights": {
            "spaced_structured": 1.0,
            "cram_then_revise": -1.0,
            "interleaved_hands_on": 0.2,
            "theory_first": 0.5,
        },
    },
    {
        "key": "pref_practice",
        "prompt": "I prefer learning by solving practice problems.",
        "weights": {
            "interleaved_hands_on": 1.2,
            "spaced_structured": 0.4,
            "theory_first": -0.6,
        },
    },
    {
        "key": "topic_switching",
        "prompt": "I am comfortable switching topics frequently within a study session.",
        "weights": {
            "interleaved_hands_on": 1.3,
            "spaced_structured": 0.3,
            "cram_then_revise": -0.5,
        },
    },
    {
        "key": "cram_history",
        "prompt": "Cramming close to an exam has worked well for me in the past.",
        "weights": {
            "cram_then_revise": 1.5,
            "spaced_structured": -0.6,
            "interleaved_hands_on": -0.2,
        },
    },
    {
        "key": "structure_need",
        "prompt": "I prefer having a predictable, structured plan.",
        "weights": {
            "spaced_structured": 1.4,
            "cram_then_revise": 0.1,
            "interleaved_hands_on": -0.4,
        },
    },
    {
        "key": "hands_on_confidence",
        "prompt": "Hands-on activities (labs, drills) help me retain information.",
        "weights": {
            "interleaved_hands_on": 1.4,
            "theory_first": -0.5,
        },
    },
    {
        "key": "reading_preference",
        "prompt": "I like to read theory or notes before attempting problems.",
        "weights": {
            "theory_first": 1.5,
            "interleaved_hands_on": -0.7,
        },
    },
    {
        "key": "consistency",
        "prompt": "Keeping a consistent daily habit is realistic for me.",
        "weights": {
            "spaced_structured": 1.0,
            "interleaved_hands_on": 0.5,
            "cram_then_revise": -0.8,
        },
    },
    {
        "key": "stress_tolerance",
        "prompt": "I handle intensive last-minute study sessions well.",
        "weights": {
            "cram_then_revise": 1.2,
            "spaced_structured": -0.5,
        },
    },
    {
        "key": "group_work",
        "prompt": "Collaborative or interactive study sessions energize me.",
        "weights": {
            "interleaved_hands_on": 0.8,
            "spaced_structured": 0.3,
            "theory_first": -0.2,
        },
    },
]


def score_questionnaire(payload: QuestionnaireIn) -> QuestionnaireOut:
    answers = payload.answers or {}
    scores: Dict[str, float] = {style: 1.0 for style in STYLES}

    for question in QUESTION_BANK:
        key = question["key"]
        if key not in answers:
            continue
        try:
            value = int(answers[key])
        except (TypeError, ValueError):
            continue
        delta = value - 3  # centre on neutral
        for style, weight in question.get("weights", {}).items():
            scores[style] = scores.get(style, 0.0) + delta * float(weight)

    min_score = min(scores.values())
    if min_score < 0:
        scores = {style: score - min_score for style, score in scores.items()}

    total = sum(scores.values()) or len(STYLES)
    weights = {style: (score / total) for style, score in scores.items()}

    preferred = payload.style
    if preferred not in STYLES and preferred != "auto":
        preferred = "spaced_structured"

    best_style = max(weights.items(), key=lambda item: item[1])[0]
    if preferred and preferred in STYLES and preferred != "auto":
        best_style = preferred

    return QuestionnaireOut(style=best_style, weights=weights)
