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

HELD_OUT = json.loads('[[[], []], [[0], [0]], [[20], [20]], [[1], [1]], [[0, 20], [20, 0]], [[20, 0], [0, 20]], [[0, 0, 20], [20, 0, 0]], [[20, 20, 0], [0, 20, 20]], [[18], [18]], [[15, 15, 4, 20, 10, 20, 20, 3], [3, 20, 20, 10, 20, 4, 15, 15]], [[4, 8, 18], [18, 8, 4]], [[12, 7, 20, 12], [12, 20, 7, 12]], [[8], [8]], [[20, 16, 6], [6, 16, 20]], [[10, 5], [5, 10]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
