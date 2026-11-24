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

VISIBLE = json.loads('[[[41, 8], 1], [[2, 48], 2], [[18, 16], 2], [[15, 9], 6], [[48, 7], 6], [[44, 48], 44], [[35, 6], 5], [[38, 28], 10]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
