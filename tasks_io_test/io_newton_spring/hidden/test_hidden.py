import json

import pytest

from program import process_sequence

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

HELD_OUT = json.loads('[[[4, 4, 3, 2], [4, 8, 11, 13]], [[-3, 5, 0, 5, 5, -4, 5, -2, -3, -1], [-3, 2, 2, 7, 12, 8, 13, 11, 8, 7]], [[-1, 1, -2], [-1, 0, -2]], [[-4, -1, -5, -2, 5, 3, -2, -3, 5], [-4, -5, -10, -12, -7, -4, -6, -9, -4]], [[-3, -4, 3, 4, 2, 0, -3, 5], [-3, -7, -4, 0, 2, 2, -1, 4]], [[2, -5, -5, -2, -4, 5, -2, 1, -1, 3], [2, -3, -8, -10, -14, -9, -11, -10, -11, -8]], [[-5, -3, 2, -4, 1, 4, 3, -3], [-5, -8, -6, -10, -9, -5, -2, -5]], [[-2, -4, -5, -2, -5, 3], [-2, -6, -11, -13, -18, -15]], [[-3, -2, 2, 4, 0, 2, -4], [-3, -5, -3, 1, 1, 3, -1]], [[1, 3, -4], [1, 4, 0]], [[4, -4, -5, -1, 1, 3, -1, 2, -5], [4, 0, -5, -6, -5, -2, -3, -1, -6]], [[-5, -5, 2, -4, 5, -4, -1, -4, -4, 3], [-5, -10, -8, -12, -7, -11, -12, -16, -20, -17]], [[0, -3, 1, 1, -3, 2, 3, -5, 3, -1], [0, -3, -2, -1, -4, -2, 1, -4, -1, -2]], [[-1, 2, -5, -3], [-1, 1, -4, -7]], [[4, -1, 4, -2, 0, -5, 4, 2, 3, -5], [4, 3, 7, 5, 5, 0, 4, 6, 9, 4]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
