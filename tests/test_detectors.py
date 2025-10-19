import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_memory.db")

from backend.utils.detectors import classify_numeric_near_miss, classify_sign_flip
from app.detectors import classify_mistake


def test_classify_numeric_near_miss():
    assert classify_numeric_near_miss(9.8, 10.0)
    assert not classify_numeric_near_miss(8.0, 10.0)


def test_classify_sign_flip():
    assert classify_sign_flip(-5, 5)
    assert not classify_sign_flip(5, 5)


def test_classify_mistake_rounding_vs_near():
    rounding = classify_mistake("", "3.14", "3.1416", {})
    assert rounding == "rounding"

    near = classify_mistake("", "9.6", "10.0", {})
    assert near == "near_miss"
