import json

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

HELD_OUT = json.loads('[[[[0, 0], [1, 1], [2, 2], [3, 3]], 4], [[[0, 0], [1, 2], [2, 4], [3, 6]], 4], [[[0, 0], [1, 1], [2, 3]], 0], [[[-2, -1], [0, 0], [2, 1], [4, 2]], 4], [[[-15, 16], [16, 14], [11, 10], [-12, 0], [-14, -8], [-11, -4], [16, -17]], 0], [[[-4, 5], [-6, 20], [5, -16], [-3, -19], [-8, 12], [-7, -9], [1, -10]], 0], [[[15, 18], [9, 3]], 0], [[[11, 9], [-20, -17], [-5, -13]], 0], [[[-6, 5], [-3, 12], [2, -18], [-10, 9], [-14, 7], [19, 15], [-10, -7]], 2], [[[-14, -17], [-7, -19], [13, 20]], 0], [[[-11, -5], [10, 17], [1, 9], [-14, -18]], 0], [[[13, -15], [4, 16], [-14, -17], [-3, 4], [13, -1]], 0], [[[-17, 19], [9, -18], [-17, 9], [-14, -14], [-4, -15]], 0], [[[15, 11], [0, -11]], 0], [[[5, -10], [8, 14], [-18, 12], [-1, 19], [13, -14]], 0]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
