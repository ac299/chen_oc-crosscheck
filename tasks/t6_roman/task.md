`roman.py` has `to_roman(n)` and `from_roman(s)`. `from_roman` accepts many invalid numerals and `to_roman` accepts out-of-range input. Fix both functions.

- `to_roman(n)` accepts an int from 1 to 3999 inclusive and returns the canonical numeral in upper case (for example `1994 -> "MCMXCIV"`). Anything else, including `bool`, floats and ints outside the range, raises `ValueError`.
- `from_roman(s)` accepts only canonical numerals, meaning exactly the strings that `to_roman` can produce. Lower case is not accepted. It raises `ValueError` for everything else, for example `"IIII"`, `"VV"`, `"IC"`, `"IL"`, `"XM"`, `"MMMM"`, `"IIV"`, `"VX"`, `"CMCM"`, `""`, `" X"` and any non-string value.
- For every valid `n`, `from_roman(to_roman(n)) == n`.

Run the tests with `python -m pytest -q`.
