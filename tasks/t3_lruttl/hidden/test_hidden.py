import pytest

from lruttl import TTLCache


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make(cap=2, ttl=10):
    clk = Clock()
    return TTLCache(cap, ttl, clock=clk), clk


def test_lru_eviction_respects_get():
    c, _ = make()
    c.set("a", 1)
    c.set("b", 2)
    assert c.get("a") == 1
    c.set("c", 3)
    assert c.keys() == ["a", "c"]


def test_expiry_boundary_inclusive():
    c, clk = make()
    c.set("a", 1)
    clk.now += 9.999
    assert c.get("a") == 1
    clk.now = 110.0
    assert c.get("a") is None
    assert c.get("a", "d") == "d"


def test_get_does_not_refresh_ttl():
    c, clk = make()
    c.set("a", 1)
    clk.now += 6
    c.get("a")
    clk.now += 6
    assert "a" not in c


def test_set_overwrite_refreshes_ttl_and_recency():
    c, clk = make()
    c.set("a", 1)
    c.set("b", 2)
    clk.now += 6
    c.set("a", 9)
    clk.now += 6
    assert c.get("a") == 9
    assert "b" not in c


def test_overwrite_at_capacity_does_not_evict():
    c, _ = make()
    c.set("a", 1)
    c.set("b", 2)
    c.set("a", 3)
    assert sorted(c.keys()) == ["a", "b"]


def test_expired_entries_do_not_count():
    c, clk = make()
    c.set("a", 1)
    clk.now += 5
    c.set("b", 2)
    clk.now += 6
    c.set("c", 3)
    assert c.keys() == ["b", "c"]
    assert len(c) == 2


def test_len_and_contains_ignore_expired_and_keep_recency():
    c, clk = make()
    c.set("a", 1)
    c.set("b", 2)
    assert "a" in c
    c.set("c", 3)
    assert c.keys() == ["b", "c"]
    clk.now += 20
    assert len(c) == 0
    assert c.keys() == []


def test_delete():
    c, clk = make()
    c.set("a", 1)
    assert c.delete("a") is True
    assert c.delete("a") is False
    c.set("b", 2)
    clk.now += 10
    assert c.delete("b") is False


@pytest.mark.parametrize("cap,ttl", [(0, 1), (-1, 1), (1, 0), (1, -5)])
def test_invalid_args(cap, ttl):
    with pytest.raises(ValueError):
        TTLCache(cap, ttl, clock=Clock())


def test_uses_injected_clock_only():
    c, clk = make(cap=1, ttl=1)
    c.set("a", 1)
    clk.now += 0.5
    assert c.get("a") == 1
