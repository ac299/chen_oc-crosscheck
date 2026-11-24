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

HELD_OUT = json.loads('[[[], true], [[-5], false], [[10], true], [[0], false], [[1], true], [[-5, 10], false], [[10, -5], false], [[-5, -5, 10], false], [[10, 10, -5], false], [[-1, 5, -2, 1, -1, 3, -4], false], [[7, 2, 7, -3], false], [[-5, 1, 1, 0], false], [[0, -3, 9, 6, -1], false], [[9, -5, -4, 2, -2, 2, 7], false], [[6, -4, 0, 9], false]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process(inp), out)
