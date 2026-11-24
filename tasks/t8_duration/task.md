Implement `parse_duration(text)` and `format_duration(seconds)` in `duration.py`.

`parse_duration(text)` converts a duration string into an int number of seconds.
- The format is one or more `<number><unit>` parts with no spaces, units in strictly descending order, each unit at most once. Units: `w` (604800 s), `d` (86400), `h` (3600), `m` (60), `s` (1). Example: `"1h30m"` is 5400 and `"2w3d"` is 1468800.
- Numbers are non-negative decimal integers without a sign. Leading zeros are allowed (`"05m"` is 300).
- An optional single leading `-` makes the whole duration negative (`"-1h"` is -3600). `"-0s"` is 0.
- Raise `ValueError` for anything else: an empty string, a unit out of order or repeated (`"30m1h"`, `"1h1h"`), a number without a unit or a unit without a number (`"10"`, `"h"`), whitespace anywhere, upper-case units, signs other than one leading `-`, or a non-string argument.

`format_duration(seconds)` converts an int back to the shortest canonical string.
- Use the largest units first and omit zero parts: 5400 becomes `"1h30m"`, 90061 becomes `"1d1h1m1s"`.
- `0` becomes `"0s"`. Negative values get a single leading `-` (`-3600` becomes `"-1h"`).
- Raise `TypeError` for anything that is not an int (`bool` is rejected).

For every int `x`, `parse_duration(format_duration(x)) == x`.

Run the tests with `python -m pytest -q`.
