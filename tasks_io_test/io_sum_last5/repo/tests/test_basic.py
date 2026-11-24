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

VISIBLE = json.loads('[[[0, 8, 7, 7], [0, 8, 15, 22]], [[3, 17, 2, 18, 13], [3, 20, 22, 40, 53]], [[0, 2, 6], [0, 2, 8]], [[16, 19, 0, 17, 6, 20], [16, 35, 35, 52, 58, 62]], [[7, 14, 18, 8, 0, 5, 13, 10, 8], [7, 21, 39, 47, 47, 45, 44, 36, 36]], [[6, 10, 3, 2, 12], [6, 16, 19, 21, 33]], [[11, 11, 19, 8], [11, 22, 41, 49]], [[14, 17, 3], [14, 31, 34]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process_sequence(inp), out)
