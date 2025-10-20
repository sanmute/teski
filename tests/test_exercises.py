from __future__ import annotations

from app.exercises import Exercise, grade


def _mcq_exercise() -> Exercise:
    return Exercise(
        id="mcq_sample",
        concept="basics",
        type="mcq",
        question="What is 2 + 2?",
        keywords=["math"],
        meta={
            "choices": [
                {"text": "4", "correct": True},
                {"text": "3"},
            ]
        },
    )


def _numeric_exercise() -> Exercise:
    return Exercise(
        id="numeric_sample",
        concept="basics",
        type="numeric",
        question="Solve x + 1 = 2.",
        keywords=["math"],
        meta={"answer": {"value": 1.0, "unit": "A", "tolerance": "abs:0.0"}},
    )


def _short_answer_exercise() -> Exercise:
    return Exercise(
        id="short_answer_sample",
        concept="physics",
        type="short_answer",
        question="Describe momentum.",
        keywords=["physics"],
        meta={
            "rubric": {
                "must_include": ["mass", "velocity"],
                "synonyms": {"velocity": ["speed"]},
                "must_not_include": ["temperature"],
                "length_max": 20,
            }
        },
    )


def test_grade_mcq_identifies_correct_choice():
    exercise = _mcq_exercise()
    ok, info = grade({"choice": 0}, exercise)
    assert ok is True
    assert info["selected"] == 0

    ok, info = grade({"choice": 1}, exercise)
    assert ok is False
    assert info["selected"] == 1
    assert info["correct_choice"] == 0


def test_grade_numeric_flags_unit_mismatch():
    exercise = _numeric_exercise()
    ok, info = grade({"value": 1.0, "unit": "V"}, exercise)
    assert ok is False
    assert info["unit_expected"] == "A"
    assert info["unit_mismatch"] is True

    ok, info = grade({"value": 1.0, "unit": "A"}, exercise)
    assert ok is True
    assert info["expected"] == 1.0


def test_grade_short_answer_accepts_synonyms():
    exercise = _short_answer_exercise()
    ok, info = grade({"text": "Momentum includes mass and speed."}, exercise)
    assert ok is True
    assert info == {}

    ok, info = grade({"text": "Too long answer mentioning temperature and skipping mass entirely."}, exercise)
    assert ok is False
    assert "missing" in info or "forbidden" in info
