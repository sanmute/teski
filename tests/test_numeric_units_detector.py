from app.numeric_units_detector import parse_value_and_unit, detect_numeric_unit_mistake


def test_parse_value_and_unit_basic():
    assert parse_value_and_unit("3.5 m") == (3.5, "m")
    assert parse_value_and_unit("2.0e-3 s") == (0.002, "s")
    assert parse_value_and_unit("42") == (42.0, None)


def test_detect_rounding_error():
    info = detect_numeric_unit_mistake(10.0, None, 10.01, None)
    assert info and info.subtype in {"rounding_error", "small_precision_error"}


def test_detect_sign_error():
    info = detect_numeric_unit_mistake(10.0, None, -10.0, None)
    assert info and info.subtype == "sign_error"


def test_detect_magnitude_error():
    info = detect_numeric_unit_mistake(10.0, None, 100.0, None)
    assert info and info.subtype == "large_magnitude_error"


def test_detect_missing_unit():
    info = detect_numeric_unit_mistake(5.0, "m", 5.0, None)
    assert info and info.family == "units" and info.subtype == "missing_unit"


def test_detect_wrong_unit_or_conversion():
    info = detect_numeric_unit_mistake(5.0, "m", 5.0, "cm")
    assert info and info.family == "units"
