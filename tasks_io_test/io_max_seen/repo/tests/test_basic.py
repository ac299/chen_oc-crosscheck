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

VISIBLE = json.loads('[[[1, 47, 17, 15], [1, 47, 47, 47]], [[8, 47, 6, 43, 47, 34], [8, 47, 47, 47, 47, 47]], [[37, 27, 2, 1], [37, 37, 37, 37]], [[13, 14, 32, 38], [13, 14, 32, 38]], [[35, 12, 45], [35, 35, 45]], [[14, 28, 37, 17, 0, 48, 10, 44, 27], [14, 28, 37, 37, 37, 48, 48, 48, 48]], [[17, 9, 13, 48, 21, 6, 5, 24], [17, 17, 17, 48, 48, 48, 48, 48]], [[22, 22, 38, 16], [22, 22, 38, 38]]]')


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process_sequence(inp), out)
