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

VISIBLE = [[[0, 8, 7, 7], [1, 0, 0, 0]], [[3, 17, 2, 18, 13], [0, 0, 0, 0, 0]], [[0, 2, 6], [1, 0, 0]], [[16, 19, 0, 17, 6, 20], [1, 0, 1, 0, 0, 0]], [[7, 14, 18, 8, 0, 5, 13, 10, 8], [0, 0, 0, 0, 1, 0, 0, 0, 0]], [[6, 10, 3, 2, 12], [0, 0, 0, 0, 0]], [[11, 11, 19, 8], [0, 0, 0, 0]], [[14, 17, 3], [0, 0, 0]]]


@pytest.mark.parametrize('inp,out', VISIBLE)
def test_visible(inp, out):
    assert _match(process_sequence(inp), out)
