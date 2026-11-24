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

VISIBLE = json.loads('[[[[-13, -19], [-3, -5], [-6, -12], [-14, 14], [-15, 17], [7, -18], [-19, -15]], 124], [[[-6, 12], [18, -19], [15, -8]], 110], [[[14, 6], [-6, 8], [17, -3], [-20, -10], [7, 1], [-3, -11], [-7, 1]], 112], [[[-15, 4], [-14, 2]], 6], [[[18, -4], [-18, 9], [14, -13], [4, -15]], 120], [[[-2, 20], [19, 3], [16, -8], [-16, -18], [-6, -2], [-15, -6]], 146], [[[4, -3], [9, 20]], 56], [[[-10, 3], [2, -7], [-3, -16], [18, 20]], 128]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process(inp), out)
