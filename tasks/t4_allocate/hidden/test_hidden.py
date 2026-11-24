import random

import pytest

from money import allocate


def test_three_way_tie_lower_index_first():
    assert allocate(100, [1, 1, 1]) == [34, 33, 33]
    assert allocate(2, [1, 1, 1]) == [1, 1, 0]


def test_largest_remainder_not_index():
    # 10 * [1, 2, 4] / 7 = 1.43, 2.86, 5.71 -> floors 1, 2, 5, leftover 2
    assert allocate(10, [1, 2, 4]) == [1, 3, 6]


def test_zero_weight_gets_zero():
    assert allocate(5, [0, 1, 1]) == [0, 3, 2]
    assert allocate(7, [0, 0, 3]) == [0, 0, 7]


def test_negative_total_mirrors():
    assert allocate(-100, [1, 1, 1]) == [-34, -33, -33]
    assert allocate(-10, [1, 2, 4]) == [-1, -3, -6]


def test_zero_total():
    assert allocate(0, [3, 1]) == [0, 0]


def test_exact_integer_arithmetic_large():
    total = 10**18 + 1
    res = allocate(total, [1, 1])
    assert res == [5 * 10**17 + 1, 5 * 10**17]


def test_random_sum_invariant():
    rng = random.Random(7)
    for _ in range(300):
        n = rng.randint(1, 6)
        w = [rng.randint(0, 9) for _ in range(n)]
        if sum(w) == 0:
            w[0] = 1
        t = rng.randint(-10_000, 10_000)
        res = allocate(t, w)
        assert sum(res) == t
        assert all(r == 0 for r, x in zip(res, w) if x == 0)


@pytest.mark.parametrize(
    "total,weights",
    [(10, []), (10, [0, 0]), (10, [1, -1]), (10.0, [1]), (10, [1.5]), (True, [1]), (10, [True])],
)
def test_invalid(total, weights):
    with pytest.raises(ValueError):
        allocate(total, weights)
