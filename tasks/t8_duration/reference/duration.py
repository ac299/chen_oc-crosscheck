"""Reference solution (never shown to agents)."""

import re

_UNITS = [("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
_PATTERN = re.compile(r"(-?)(?:([0-9]+)w)?(?:([0-9]+)d)?(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?")


def parse_duration(text):
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    m = _PATTERN.fullmatch(text)
    if not m or all(g is None for g in m.groups()[1:]):
        raise ValueError(f"invalid duration: {text!r}")
    total = sum(int(g) * size for g, (_, size) in zip(m.groups()[1:], _UNITS) if g is not None)
    return -total if m.group(1) else total


def format_duration(seconds):
    if not isinstance(seconds, int) or isinstance(seconds, bool):
        raise TypeError("seconds must be an int")
    if seconds == 0:
        return "0s"
    sign = "-" if seconds < 0 else ""
    rest = abs(seconds)
    parts = []
    for unit, size in _UNITS:
        q, rest = divmod(rest, size)
        if q:
            parts.append(f"{q}{unit}")
    return sign + "".join(parts)
