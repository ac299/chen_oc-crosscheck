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

VISIBLE = json.loads('[[[-10, -2, -3, -3], [10, -8, 1, 0]], [[-7, 7, -8, 8, 3], [7, 0, 1, 0, -5]], [[-10, -8, -4], [10, -2, -4]], [[6, 9, -10, 7, -4, 10], [6, 3, 1, -3, -3, 6]], [[-3, 4, 8, -2, -10, -5, 3, 0, -2], [3, 1, 4, -6, 8, -5, -2, -3, 2]], [[-4, 0, -7, -8, 2], [4, -4, 7, 1, -6]], [[1, 1, 9, -2], [1, 0, 8, -7]], [[4, 7, -7], [4, 3, 0]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process_sequence(inp), out)
