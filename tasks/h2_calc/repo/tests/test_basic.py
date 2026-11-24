from calc import evaluate


def test_basic():
    assert evaluate("1 + 2 * 3") == 7
    assert evaluate("(1 + 2) * 3") == 9
