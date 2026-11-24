from money import allocate


def test_even_split():
    assert allocate(100, [1, 1]) == [50, 50]


def test_sum_preserved():
    assert sum(allocate(100, [1, 1, 1])) == 100
