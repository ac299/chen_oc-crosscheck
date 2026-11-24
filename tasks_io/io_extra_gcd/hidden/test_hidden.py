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

HELD_OUT = [[[1, 1], 1], [[100, 100], 100], [[1, 100], 1], [[100, 1], 1], [[50, 33], 1], [[87, 11], 1], [[73, 74], 1], [[69, 63], 3], [[62, 17], 1], [[83, 41], 1], [[83, 83], 83], [[13, 83], 1], [[25, 20], 5], [[34, 74], 2], [[7, 90], 1]]


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
