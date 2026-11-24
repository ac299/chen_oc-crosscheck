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

VISIBLE = json.loads('[[[0, 4, 10, 1], [0, 4, 4, 1]], [[9, 6, 10, 3, 10], [9, 6, 15, 3, 18]], [[8, 6, 10, 0, 2, 5, 10], [8, 6, 14, 0, 2, 5, 7]], [[1, 1, 5, 9, 10, 8, 10, 10], [1, 1, 5, 9, 14, 8, 22, 23]], [[9, 3, 0, 4, 3, 6, 10, 10, 10], [9, 3, 0, 4, 3, 6, 9, 13, 13]], [[9, 2, 3, 10, 10], [9, 2, 3, 5, 14]], [[0, 3, 5, 1, 10, 10, 7, 10, 10], [0, 3, 5, 1, 6, 9, 7, 16, 16]], [[9, 6, 2, 1, 1, 10, 6, 6, 7, 10], [9, 6, 2, 1, 1, 2, 6, 6, 7, 13]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
