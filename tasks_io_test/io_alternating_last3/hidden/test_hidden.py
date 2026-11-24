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

HELD_OUT = json.loads('[[[3, 3, 1, 2], [0, 0, 0, 1]], [[1, 1, 2, 0], [0, 0, 0, 1]], [[3, 1, 3, 0, 2, 0, 1], [0, 0, 0, 1, 1, 0, 1]], [[1, 2, 1, 0, 3, 2], [0, 0, 0, 1, 1, 1]], [[3, 3, 0, 0, 1], [0, 0, 0, 0, 0]], [[1, 3, 2, 2], [0, 0, 1, 0]], [[1, 3, 0], [0, 0, 1]], [[1, 1, 1, 0, 0, 1, 0, 2, 1], [0, 0, 0, 0, 0, 0, 0, 1, 1]], [[3, 2, 3, 0, 0, 3], [0, 0, 0, 1, 0, 0]], [[3, 0, 0, 2], [0, 0, 0, 0]], [[2, 3, 0, 3, 0, 0, 3, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0, 0]], [[0, 0, 3, 2, 1, 3, 3], [0, 0, 0, 1, 1, 1, 0]], [[3, 0, 2, 0, 2], [0, 0, 1, 0, 0]], [[0, 1, 3, 2, 1, 2, 0, 3, 0, 3], [0, 0, 1, 1, 1, 0, 1, 1, 0, 0]], [[3, 2, 1, 2, 0, 1, 3, 2, 2], [0, 0, 1, 0, 1, 1, 1, 1, 0]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
