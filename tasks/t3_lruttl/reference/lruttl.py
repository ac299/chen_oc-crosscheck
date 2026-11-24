"""Reference solution (never shown to agents)."""

import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity, ttl, clock=time.monotonic):
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be >= 1")
        if not ttl > 0:
            raise ValueError("ttl must be > 0")
        self._cap = capacity
        self._ttl = ttl
        self._clock = clock
        self._data = OrderedDict()  # key -> (value, stored_at)

    def _purge(self):
        now = self._clock()
        for key in [k for k, (_, t) in self._data.items() if now - t >= self._ttl]:
            del self._data[key]

    def set(self, key, value):
        self._purge()
        if key in self._data:
            del self._data[key]
        elif len(self._data) >= self._cap:
            self._data.popitem(last=False)
        self._data[key] = (value, self._clock())

    def get(self, key, default=None):
        self._purge()
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key][0]

    def delete(self, key):
        self._purge()
        if key in self._data:
            del self._data[key]
            return True
        return False

    def __len__(self):
        self._purge()
        return len(self._data)

    def __contains__(self, key):
        self._purge()
        return key in self._data

    def keys(self):
        self._purge()
        return list(self._data)
