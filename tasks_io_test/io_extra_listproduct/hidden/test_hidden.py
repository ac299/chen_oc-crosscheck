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

HELD_OUT = json.loads('[[[], 1], [[1], 1], [[5], 5], [[1, 5], 5], [[5, 1], 5], [[1, 1, 5], 5], [[5, 5, 1], 25], [[4, 4, 2, 3, 1, 2, 2, 3], 1152], [[4, 2, 4, 1], 32], [[1, 2, 5, 2], 20], [[3, 2], 6], [[3, 2, 4, 4, 1, 1, 2], 192], [[2], 2], [[3, 5, 3, 1, 2, 4], 360], [[4], 4]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
