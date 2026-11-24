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

HELD_OUT = json.loads('[[[18, 18, 17, 15], [18, 36, 53, 68]], [[4, 20, 10, 20, 20, 3, 20, 6, 4, 8], [4, 24, 34, 54, 74, 73, 73, 69, 53, 41]], [[8, 12, 7], [8, 20, 27]], [[2, 8, 0, 6, 20, 16, 6, 5, 10], [2, 10, 10, 16, 36, 50, 48, 53, 57]], [[2, 17, 19, 14, 11], [2, 19, 38, 52, 63]], [[20, 15, 14, 0, 1], [20, 35, 49, 49, 50]], [[3, 20, 7, 12, 8, 16], [3, 23, 30, 42, 50, 63]], [[1, 5, 14, 3, 13, 19, 17, 5], [1, 6, 20, 23, 36, 54, 66, 57]], [[7, 3, 1, 6, 0, 16], [7, 10, 11, 17, 17, 26]], [[4, 7, 15, 18, 10, 14, 3], [4, 11, 26, 44, 54, 64, 60]], [[13, 16, 2], [13, 29, 31]], [[18, 3, 1, 8, 12, 16, 9, 15, 1], [18, 21, 22, 30, 42, 40, 46, 60, 53]], [[1, 1, 14, 3, 20, 3, 8, 2, 3, 17], [1, 2, 16, 19, 39, 41, 48, 36, 36, 33]], [[10, 4, 13, 12, 5, 14, 17, 1, 16, 9], [10, 14, 27, 39, 44, 48, 61, 49, 53, 57]], [[9, 14, 1, 4], [9, 23, 24, 28]]]')


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
