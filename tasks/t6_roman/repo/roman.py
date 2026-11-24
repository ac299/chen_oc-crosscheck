"""Roman numeral conversion."""

_VALUES = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]
_SYMBOL = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(n):
    out = []
    for value, sym in _VALUES:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


def from_roman(s):
    total = 0
    prev = 0
    for ch in reversed(s.upper()):
        value = _SYMBOL[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total
