from backend.utils.detectors import classify_numeric_near_miss, classify_sign_flip


def test_classify_numeric_near_miss():
    assert classify_numeric_near_miss(9.8, 10.0)
    assert not classify_numeric_near_miss(8.0, 10.0)


def test_classify_sign_flip():
    assert classify_sign_flip(-5, 5)
    assert not classify_sign_flip(5, 5)
