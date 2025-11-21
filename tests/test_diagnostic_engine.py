from app.diagnostic_engine import diagnose_mistake
from app.exercises import Exercise


def base_exercise(domain: str | None = None, type_: str = "short_answer") -> Exercise:
    return Exercise(
        id="ex",
        concept="Test concept",
        type=type_,
        question="Q?",
        domain=domain,
        subdomain=None,
        difficulty=1,
    )


def test_routes_to_python_detector():
    exercise = base_exercise(domain="python", type_="short_answer")
    info = diagnose_mistake(exercise, "SyntaxError: invalid syntax", "print('hi')")
    assert info is not None
    assert info.family == "python_syntax"


def test_routes_to_math_detector():
    exercise = base_exercise(domain="math", type_="numeric")
    exercise.skill_ids = ["calc_limits_1"]
    info = diagnose_mistake(exercise, {"value": -5}, {"value": 5})
    assert info is not None
    assert info.family.startswith("math")


def test_generic_detector_for_unknown_domain():
    exercise = base_exercise(domain="history", type_="short_answer")
    info = diagnose_mistake(exercise, "Wasington", "Washington")
    assert info is not None
    assert info.family in {"factual", "behavioral", "reasoning", "numeric"}


def test_generic_numeric_near_miss():
    exercise = base_exercise(domain=None, type_="numeric")
    info = diagnose_mistake(exercise, "9.99", "10")
    assert info is not None
    assert info.subtype in {"rounding_or_precision_error", "rounding_error", "small_precision_error", "large_magnitude_error", "plausible_distractor"}
