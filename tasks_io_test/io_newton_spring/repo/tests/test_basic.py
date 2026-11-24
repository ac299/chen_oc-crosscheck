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

VISIBLE = json.loads('[[[-5, -1, -2, -2], [-5, -6, -8, -10]], [[-4, 5, 3, -4, 4], [-4, 1, 4, 0, 4]], [[-5, -5, -4, -2, -2, 3, 4, -5, 3], [-5, -10, -14, -16, -18, -15, -11, -16, -13]], [[5, 3, 1, -2, 2, 4], [5, 8, 9, 7, 9, 13]], [[-5, -3, 1, 0, -1, -3, -2], [-5, -8, -7, -7, -8, -11, -13]], [[-4, -4, 1, -4, 0, 0, 4, -1], [-4, -8, -7, -11, -11, -11, -7, -8]], [[2, 3, -4], [2, 5, 1]], [[-4, 3, -1, 5, 4, 0, 4, -2, -4], [-4, -1, -2, 3, 7, 7, 11, 9, 5]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process_sequence(inp), out)
