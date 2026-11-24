"""Reference solution (never shown to agents)."""

_VALUES = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def to_roman(n):
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 3999:
        raise ValueError("n must be an int in 1..3999")
    out = []
    for value, sym in _VALUES:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


_TABLE = {to_roman(n): n for n in range(1, 4000)}


def from_roman(s):
    if not isinstance(s, str) or s not in _TABLE:
        raise ValueError(f"not a canonical roman numeral: {s!r}")
    return _TABLE[s]
