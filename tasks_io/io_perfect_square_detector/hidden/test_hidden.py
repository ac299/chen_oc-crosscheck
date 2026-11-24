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

HELD_OUT = [[[18, 18, 17, 15], [0, 0, 0, 0]], [[4, 20, 10, 20, 20, 3, 20, 6, 4, 8], [1, 0, 0, 0, 0, 0, 0, 0, 1, 0]], [[8, 12, 7], [0, 0, 0]], [[2, 8, 0, 6, 20, 16, 6, 5, 10], [0, 0, 1, 0, 0, 1, 0, 0, 0]], [[2, 17, 19, 14, 11], [0, 0, 0, 0, 0]], [[20, 15, 14, 0, 1], [0, 0, 0, 1, 1]], [[3, 20, 7, 12, 8, 16], [0, 0, 0, 0, 0, 1]], [[1, 5, 14, 3, 13, 19, 17, 5], [1, 0, 0, 0, 0, 0, 0, 0]], [[7, 3, 1, 6, 0, 16], [0, 0, 1, 0, 1, 1]], [[4, 7, 15, 18, 10, 14, 3], [1, 0, 0, 0, 0, 0, 0]], [[13, 16, 2], [0, 1, 0]], [[18, 3, 1, 8, 12, 16, 9, 15, 1], [0, 0, 1, 0, 0, 1, 1, 0, 1]], [[1, 1, 14, 3, 20, 3, 8, 2, 3, 17], [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]], [[10, 4, 13, 12, 5, 14, 17, 1, 16, 9], [0, 1, 0, 0, 0, 0, 0, 1, 1, 1]], [[9, 14, 1, 4], [1, 0, 1, 1]]]


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
