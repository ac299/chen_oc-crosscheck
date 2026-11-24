import pytest

from program import process

def _match(actual, expected):
    if isinstance(expected, list) and isinstance(actual, (list, tuple)):
        return len(expected) == len(actual) and all(_match(a, e) for a, e in zip(actual, expected))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(_match(actual[k], expected[k]) for k in expected)
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return actual == expected if isinstance(expected, int) else abs(actual - expected) < 1e-6
    return actual == expected

VISIBLE = [[[[20, -13], [-19, -3]], 1621], [[[-5, -6], [-12, -14]], 113], [[[14, -15], [17, 7]], 493], [[[-18, -19], [-15, -7]], 153], [[[-6, 12], [18, -19]], 1537], [[[15, -8], [14, 6]], 197], [[[-6, 8], [17, -3]], 650], [[[-20, -10], [7, 1]], 850]]


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
