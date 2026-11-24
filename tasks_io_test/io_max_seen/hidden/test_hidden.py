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

HELD_OUT = json.loads('[[[36, 36, 34, 31], [36, 36, 36, 36]], [[8, 41, 20, 41, 50, 41, 6, 41, 12, 9], [8, 41, 41, 41, 50, 50, 50, 50, 50, 50]], [[36, 3, 44, 49, 16, 25, 50], [36, 36, 44, 49, 49, 49, 50]], [[40, 25, 4, 17, 1, 12], [40, 40, 40, 40, 40, 40]], [[11, 43, 21, 10, 5, 35], [11, 43, 43, 43, 43, 43]], [[44, 47, 23, 8, 42, 41, 31, 29, 0, 47], [44, 47, 47, 47, 47, 47, 47, 47, 47, 47]], [[15, 7, 46], [15, 15, 46]], [[25, 50, 17, 32, 22, 2], [25, 50, 50, 50, 50, 50]], [[29, 6, 27, 39, 35], [29, 29, 29, 39, 39]], [[13, 14, 6, 50, 3], [13, 14, 14, 50, 50]], [[1, 33, 40, 18, 9, 15], [1, 33, 40, 40, 40, 40]], [[37, 21, 29, 6, 2, 26, 33, 5, 49, 24], [37, 37, 37, 37, 37, 37, 37, 37, 49, 49]], [[44, 3, 17, 24], [44, 44, 44, 44]], [[49, 31, 3, 39, 49, 29, 2], [49, 49, 49, 49, 49, 49, 49]], [[29, 50, 6], [29, 50, 50]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
