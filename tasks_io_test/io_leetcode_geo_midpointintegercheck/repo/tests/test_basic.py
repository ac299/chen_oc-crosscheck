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

VISIBLE = json.loads('[[[[20, -13], [-19, -3]], false], [[[-5, -6], [-12, -14]], false], [[[14, -15], [17, 7]], false], [[[-18, -19], [-15, -7]], false], [[[-6, 12], [18, -19]], false], [[[15, -8], [14, 6]], false], [[[-6, 8], [17, -3]], false], [[[-20, -10], [7, 1]], false]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
