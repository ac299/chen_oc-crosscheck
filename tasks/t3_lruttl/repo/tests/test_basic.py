from lruttl import TTLCache


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_set_get():
    c = TTLCache(2, 10, clock=Clock())
    c.set("a", 1)
    assert c.get("a") == 1
    assert c.get("b") is None
