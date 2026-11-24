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

VISIBLE = json.loads('[[[7, 7, 4, 3], [3, 4, 7, 7]], [[2, 18, 13, 1, 0, 2, 6, 7], [7, 6, 2, 0, 1, 13, 18, 2]], [[19, 0, 17, 6, 20, 17, 13, 7], [7, 13, 17, 20, 6, 17, 0, 19]], [[18, 8, 0, 5, 13, 10, 8], [8, 10, 13, 5, 0, 8, 18]], [[6, 10], [10, 6]], [[2], [2]], [[3, 11, 11, 19, 8, 1], [1, 8, 19, 11, 11, 3]], [[17, 3, 12, 2, 17, 9, 20], [20, 9, 17, 2, 12, 3, 17]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
