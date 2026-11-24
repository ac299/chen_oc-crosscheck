"""Specification tests for money.allocate (largest-remainder allocation)."""

import pytest

from money import allocate


# r1: basic even split
def test_r1_basic_even_split():
    assert allocate(100, [1, 1]) == [50, 50]


# r2: length preserved and sum exact
def test_r2_length_and_sum_exact():
    result = allocate(100, [1, 1, 1])
    assert len(result) == 3
    assert sum(result) == 100
    assert result == [34, 33, 33]

    result = allocate(10, [1, 2, 3, 4])
    assert len(result) == 4
    assert sum(result) == 10
    assert result == [1, 2, 3, 4]

    result = allocate(0, [5, 5])
    assert len(result) == 2
    assert sum(result) == 0
    assert result == [0, 0]


# r3: floor base shares
def test_r3_floor_base_shares():
    assert allocate(7, [1, 2, 4]) == [1, 2, 4]
    assert allocate(100, [1, 2, 3]) == [17, 33, 50]
    assert allocate(10, [1, 1, 1]) == [4, 3, 3]


# r4: leftover cents to largest fractional remainders
def test_r4_largest_remainder_distribution():
    assert allocate(10, [1, 1, 1]) == [4, 3, 3]
    assert allocate(100, [1, 2, 3]) == [17, 33, 50]
    assert allocate(5, [1, 1, 1, 1]) == [2, 1, 1, 1]


# r5: ties broken by lower index
def test_r5_ties_lower_index():
    assert allocate(10, [1, 1, 1]) == [4, 3, 3]
    assert allocate(2, [1, 1, 1]) == [1, 1, 0]
    assert allocate(1, [1, 1, 1]) == [1, 0, 0]


# r6: negative total mirrors positive split
def test_r6_negative_total():
    assert allocate(-100, [1, 1]) == [-50, -50]
    assert allocate(-10, [1, 1, 1]) == [-4, -3, -3]
    assert allocate(-100, [1, 2, 3]) == [-17, -33, -50]
    assert allocate(-1, [1, 1, 1]) == [-1, 0, 0]


# r7: zero total yields all zeros
def test_r7_zero_total():
    assert allocate(0, [1, 2, 3]) == [0, 0, 0]
    assert allocate(0, [7]) == [0]
    assert allocate(0, [0, 1]) == [0, 0]


# r8: zero weight always gets zero
def test_r8_zero_weight_gets_zero():
    assert allocate(10, [0, 1, 1]) == [0, 5, 5]
    assert allocate(10, [1, 0, 1, 1]) == [4, 0, 3, 3]
    assert allocate(1, [0, 0, 1]) == [0, 0, 1]
    assert allocate(-10, [0, 1, 1]) == [0, -5, -5]


# r9: single recipient gets whole total
def test_r9_single_recipient():
    assert allocate(100, [5]) == [100]
    assert allocate(-7, [3]) == [-7]
    assert allocate(0, [1]) == [0]


# r10: non-int total raises ValueError
def test_r10_non_int_total():
    with pytest.raises(ValueError):
        allocate(1.5, [1, 1])
    with pytest.raises(ValueError):
        allocate("100", [1, 1])
    with pytest.raises(ValueError):
        allocate(None, [1, 1])


# r11: bool total raises ValueError
def test_r11_bool_total():
    with pytest.raises(ValueError):
        allocate(True, [1, 1])
    with pytest.raises(ValueError):
        allocate(False, [1, 1])


# r12: empty weights raises ValueError
def test_r12_empty_weights():
    with pytest.raises(ValueError):
        allocate(100, [])
    with pytest.raises(ValueError):
        allocate(0, [])


# r13: weights summing to zero raise ValueError
def test_r13_zero_sum_weights():
    with pytest.raises(ValueError):
        allocate(100, [0, 0])
    with pytest.raises(ValueError):
        allocate(0, [0])
    with pytest.raises(ValueError):
        allocate(-5, [0, 0, 0])


# r14: negative weights raise ValueError
def test_r14_negative_weights():
    with pytest.raises(ValueError):
        allocate(100, [1, -1])
    with pytest.raises(ValueError):
        allocate(100, [-1, 2])
    with pytest.raises(ValueError):
        allocate(0, [-3])


# r15: non-int weight elements raise ValueError
def test_r15_non_int_weights():
    with pytest.raises(ValueError):
        allocate(100, [1.0, 1])
    with pytest.raises(ValueError):
        allocate(100, [1, "2"])
    with pytest.raises(ValueError):
        allocate(100, [None, 1])


# r16: bool weight elements raise ValueError
def test_r16_bool_weights():
    with pytest.raises(ValueError):
        allocate(100, [True, True])
    with pytest.raises(ValueError):
        allocate(100, [1, False])


# r17: exact integer arithmetic with large values
def test_r17_exact_large_integers():
    assert allocate(10**18 + 1, [1, 1]) == [500000000000000001, 500000000000000000]
    assert allocate(3, [10**18, 10**18]) == [2, 1]
    assert allocate(100, [1, 3]) == [25, 75]


# r18: all result elements are plain ints
def test_r18_result_element_types():
    result = allocate(10, [1, 2, 3])
    assert [type(x) for x in result] == [int, int, int]
    for x in allocate(100, [1, 1]):
        assert isinstance(x, int)
        assert not isinstance(x, bool)


# r19: zero weights with leftover cents among positive weights
def test_r19_zero_weight_with_leftover():
    assert allocate(7, [0, 1, 2]) == [0, 2, 5]
    assert allocate(100, [0, 1, 1, 1]) == [0, 34, 33, 33]


# r20: negative total with zero weights mirrors positive split
def test_r20_negative_with_zero_weights():
    assert allocate(-7, [0, 1, 2]) == [0, -2, -5]
    assert allocate(-2, [1, 1, 1]) == [-1, -1, 0]


# r21: total smaller than number of recipients
def test_r21_small_total_boundary():
    assert allocate(1, [1, 1, 1, 1]) == [1, 0, 0, 0]
    assert allocate(2, [1, 1, 1, 1]) == [1, 1, 0, 0]
    assert allocate(-1, [1, 1, 1, 1]) == [-1, 0, 0, 0]


# r22: exact division leaves no leftover
def test_r22_exact_division_no_leftover():
    assert allocate(6, [1, 2, 3]) == [1, 2, 3]
    assert allocate(-6, [1, 2, 3]) == [-1, -2, -3]
    assert allocate(100, [1, 1, 2]) == [25, 25, 50]


# r23: at most one extra cent per recipient
def test_r23_max_leftover_one_extra_each():
    assert allocate(5, [1, 1, 1]) == [2, 2, 1]
    assert allocate(100, [1, 1, 1]) == [34, 33, 33]
