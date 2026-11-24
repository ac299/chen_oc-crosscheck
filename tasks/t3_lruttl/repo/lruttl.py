"""LRU cache with per-entry expiry."""

import time


class TTLCache:
    def __init__(self, capacity, ttl, clock=time.monotonic):
        raise NotImplementedError
