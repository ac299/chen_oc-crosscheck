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

HELD_OUT = [[[16, 16, 14, 11], [16, 16, 14, 11]], [[-12, 0, -14, -8, -11, -4, 16, -17, -4, 5], [12, 0, 14, 8, 11, 4, 16, 17, 4, 5]], [[20, 5, -16, -3, -19, -8], [20, 5, 16, 3, 19, 8]], [[-9, 1, -10, -15, 15, 18], [9, 1, 10, 15, 15, 18]], [[3, -12, 11, 9, -20, -17, -5, -13, -6, 5], [3, 12, 11, 9, 20, 17, 5, 13, 6, 5]], [[12, 2, -18, -10, 9, -14, 7], [12, 2, 18, 10, 9, 14, 7]], [[-7, -6, -14, -17, -7], [7, 6, 14, 17, 7]], [[13, 20, -2], [13, 20, 2]], [[-5, 10, 17, 1, 9], [5, 10, 17, 1, 9]], [[-18, 6, 13, -15], [18, 6, 13, 15]], [[16, -14, -17, -3, 4, 13, -1, 11, -17], [16, 14, 17, 3, 4, 13, 1, 11, 17]], [[-18, -17, 9, -14, -14, -4, -15, -14, 15, 11], [18, 17, 9, 14, 14, 4, 15, 14, 15, 11]], [[-11, 7, 5, -10, 8, 14, -18, 12], [11, 7, 5, 10, 8, 14, 18, 12]], [[19, 13, -14, -1, 8, -17, -12], [19, 13, 14, 1, 8, 17, 12]], [[17, -3, 18, -6, 2, -18, 16, 11, 13, -20], [17, 3, 18, 6, 2, 18, 16, 11, 13, 20]]]


@pytest.mark.parametrize('inp,out', HELD_OUT)
def test_held_out(inp, out):
    assert _match(process_sequence(inp), out)
