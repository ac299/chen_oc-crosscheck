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

HELD_OUT = json.loads('[[[6, 4, 4, 4], [0, 4, 2, 0]], [[3, 1, 6, 5, 2, 5, 6, 5, 6, 6], [3, 4, 4, 3, 5, 4, 4, 3, 3, 3]], [[5, 6, 1, 1], [5, 5, 0, 1]], [[4, 0, 5, 6, 2, 3, 6], [4, 4, 3, 3, 5, 2, 2]], [[6, 5, 3, 0, 2, 0], [0, 5, 2, 2, 4, 4]], [[5, 6, 4, 1, 1, 6], [5, 5, 3, 4, 5, 5]], [[1, 0, 4, 4, 3, 5, 5, 2], [1, 1, 5, 3, 0, 5, 4, 0]], [[5, 5, 3, 3, 0], [5, 4, 1, 4, 4]], [[1, 0, 5], [1, 1, 0]], [[3, 6, 2, 6, 4, 2], [3, 3, 5, 5, 3, 5]], [[6, 1, 3], [0, 1, 4]], [[3, 4, 4, 6], [3, 1, 5, 5]], [[1, 1, 0, 6, 0], [1, 2, 2, 2, 2]], [[0, 4, 5, 2, 1, 1], [0, 4, 3, 5, 0, 1]], [[4, 2, 6, 3, 0, 6, 0, 3, 4, 0], [4, 0, 0, 3, 3, 3, 3, 0, 4, 4]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
