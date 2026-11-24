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

HELD_OUT = json.loads('[[[8, 8, 7, 5], [8, 0, -1, -2]], [[-6, 10, 0, 10, 10, -7, 10, -4, -6, -2], [6, 4, -10, 10, 0, -3, 3, -6, 2, -4]], [[-2, 2, -3], [2, 0, 1]], [[-8, -2, -10, -4, 10, 6, -4, -5, 0], [8, -6, 8, -6, 6, -4, -2, 1, -5]], [[-8, 7, 9, 4, 1], [8, -1, 2, -5, -3]], [[10, 5, 4, -10, -9], [10, -5, -1, 6, -1]], [[-7, 10, -3, 2, -2, 6], [7, 3, -7, -1, 0, 4]], [[-9, -5, 4, -7, 3, 9, 7, -5], [9, -4, -1, 3, -4, 6, -2, -2]], [[-3, -7, -9, -4, -10, 6], [3, 4, 2, -5, 6, -4]], [[-6, -3, 5, 8, 0, 4, -7], [6, -3, 2, 3, -8, 4, 3]], [[3, 6, -8], [3, 3, 2]], [[8, -7, -9, -2, 2, 6, -1, 5, -9], [8, -1, 2, -7, 0, 4, -5, 4, 4]], [[-9, -9, 4, -7, 10, -7, -2, -8, -7, 7], [9, 0, -5, 3, 3, -3, -5, 6, -1, 0]], [[0, -6, 3, 2, -5, 4, 7, -9, 6, -1], [0, 6, -3, -1, 3, -1, 3, 2, -3, -5]], [[-1, 4, -9, -6], [1, 3, 5, -3]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
