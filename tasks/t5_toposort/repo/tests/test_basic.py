from toposort import build_order


def test_chain():
    assert build_order({"b": ["a"], "c": ["b"]}) == ["a", "b", "c"]
