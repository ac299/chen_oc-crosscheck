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

HELD_OUT = [[[[0, 0], [0, 0]], 0], [[[0, 0], [1, 1]], 2], [[[-1, -1], [2, 3]], 25], [[[-20, 20], [20, -20]], 3200], [[[-5, 7], [8, -6]], 338], [[[-15, 16], [16, 14]], 965], [[[11, 10], [-12, 0]], 629], [[[-14, -8], [-11, -4]], 25], [[[16, -17], [-4, 5]], 884], [[[-6, 20], [5, -16]], 1417], [[[-3, -19], [-8, 12]], 986], [[[-7, -9], [1, -10]], 65], [[[-15, 15], [18, 9]], 1125], [[[3, -12], [11, 9]], 505], [[[-20, -17], [-5, -13]], 241]]


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
