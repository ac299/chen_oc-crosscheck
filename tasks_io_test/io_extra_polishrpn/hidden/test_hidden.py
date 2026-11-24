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

HELD_OUT = json.loads('[[[3, 4, 10], [3, 4, 7]], [[1, 2, 10, 3, 10], [1, 2, 3, 3, 6]], [[1, 2, 3, 10, 10], [1, 2, 3, 5, 6]], [[9, 9, 7, 10], [9, 9, 7, 16]], [[3, 2, 10, 4, 10], [3, 2, 5, 4, 9]], [[1, 4, 10, 8, 10, 2, 1, 9, 5, 10, 10, 10], [1, 4, 5, 8, 13, 2, 1, 9, 5, 14, 15, 17]], [[6, 4, 5, 10, 1, 9, 10, 10], [6, 4, 5, 9, 1, 9, 10, 19]], [[0, 8, 2, 10, 1, 0, 10], [0, 8, 2, 10, 1, 0, 1]], [[0, 4, 4, 7, 10, 10], [0, 4, 4, 7, 11, 15]], [[1, 4, 1, 5, 10, 10, 10], [1, 4, 1, 5, 6, 10, 11]], [[4, 7, 10, 7, 10], [4, 7, 11, 7, 18]], [[0, 9, 0, 7, 9, 10, 7, 10, 10], [0, 9, 0, 7, 9, 16, 7, 23, 23]], [[0, 5, 10, 9, 5, 6, 6, 5, 10, 0], [0, 5, 5, 9, 5, 6, 6, 5, 11, 0]], [[4, 8, 6, 2, 9, 3, 1, 2, 10], [4, 8, 6, 2, 9, 3, 1, 2, 3]], [[2, 4, 9, 10, 0, 6], [2, 4, 9, 13, 0, 6]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
