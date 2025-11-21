from app.exercises import Exercise
from app.math_mistake_detector import detect_math_mistake_type


def test_detects_sign_error_numeric():
    exercise = Exercise(
        id="ex1",
        concept="Linear equations",
        type="numeric",
        question="Solve for x",
    )
    mistake = detect_math_mistake_type(exercise, {"value": -4}, {"value": 4}, ["alg_linear_equations_1"])
    assert mistake and mistake.subtype == "sign_error"


def test_detects_rounding_precision_error():
    exercise = Exercise(
        id="ex2",
        concept="Percent error",
        type="numeric",
        question="Compute value",
    )
    mistake = detect_math_mistake_type(exercise, {"value": 9.99}, {"value": 10.0}, ["alg_operations_1"])
    assert mistake and mistake.subtype == "rounding_or_precision_error"


def test_derivative_rule_error_when_power_off():
    exercise = Exercise(
        id="ex3",
        concept="Derivative of polynomial",
        type="short_answer",
        question="Find the derivative",
    )
    mistake = detect_math_mistake_type(exercise, "x^3", "3x^2", ["calc_derivatives_1"])
    assert mistake and mistake.subtype == "derivative_rule_error"


def test_limit_evaluation_error_for_infinite_limit():
    exercise = Exercise(
        id="ex4",
        concept="Limit at infinity",
        type="numeric",
        question="Compute limit",
    )
    mistake = detect_math_mistake_type(exercise, {"value": 0}, float("inf"), ["calc_limits_1"])
    assert mistake and mistake.subtype == "limit_evaluation_error"


def test_none_when_no_rule_matches():
    exercise = Exercise(
        id="ex5",
        concept="Area",
        type="numeric",
        question="Compute area",
    )
    mistake = detect_math_mistake_type(exercise, {"value": 2}, {"value": 5}, ["geometry_basic"])
    assert mistake is None
