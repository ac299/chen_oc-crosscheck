import copy

import pytest

from toposort import CycleError, build_order


def test_lexicographic_smallest():
    deps = {"d": ["b", "c"], "b": ["a"], "c": ["a"], "e": []}
    assert build_order(deps) == ["a", "b", "c", "d", "e"]


def test_ready_set_reconsidered_after_each_pick():
    # after "a", "z" becomes ready but "b" is smaller
    deps = {"z": ["a"], "b": [], "a": []}
    assert build_order(deps) == ["a", "b", "z"]
    deps2 = {"c": ["b"], "b": [], "a": ["c"]}
    assert build_order(deps2) == ["b", "c", "a"]


def test_prerequisite_only_nodes_and_duplicates():
    assert build_order({"x": ["y", "y", "w"]}) == ["w", "y", "x"]


def test_empty():
    assert build_order({}) == []


def test_input_not_modified():
    deps = {"b": ["a"], "c": ["a", "b"]}
    before = copy.deepcopy(deps)
    build_order(deps)
    assert deps == before


def test_accepts_tuples_and_sets():
    assert build_order({"b": ("a",), "c": {"b"}}) == ["a", "b", "c"]


def test_cycle_is_value_error():
    with pytest.raises(ValueError):
        build_order({"a": ["b"], "b": ["a"]})


def test_cycle_nodes_exclude_hangers_on():
    deps = {"a": ["b"], "b": ["c", "a0"], "c": ["a"], "d": ["a"], "c2": [], "a0": []}
    with pytest.raises(CycleError) as info:
        build_order(deps)
    assert info.value.nodes == ["a", "b", "c"]


def test_self_loop_and_two_cycles():
    deps = {"s": ["s"], "p": ["q"], "q": ["p"], "r": ["p"], "t": []}
    with pytest.raises(CycleError) as info:
        build_order(deps)
    assert info.value.nodes == ["p", "q", "s"]


def test_cycle_downstream_of_dag():
    deps = {"m": ["n"], "n": ["m", "base"], "base": []}
    with pytest.raises(CycleError) as info:
        build_order(deps)
    assert info.value.nodes == ["m", "n"]
