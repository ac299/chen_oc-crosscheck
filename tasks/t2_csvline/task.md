Implement `parse_line(line, delimiter=",")` in `csvline.py`. It parses one CSV record and returns a list of field strings. Do not use the `csv` module.

Rules:
- Fields are separated by `delimiter` (a single character). An empty line returns `[""]`. A trailing delimiter produces a trailing empty field (`"a,"` gives `["a", ""]`).
- Whitespace is significant and is never stripped.
- A field that starts with `"` is quoted. Inside it, a delimiter is ordinary text and `""` stands for one literal `"`. The closing quote must be followed immediately by the delimiter or the end of the line; anything else raises `ValueError`. A quoted field that never closes raises `ValueError`.
- In an unquoted field a `"` is an ordinary character (`ab"c` stays `ab"c`).
- A line may end with `\n` or `\r\n`; that line ending is removed first. Newlines inside quoted fields are not supported.
- `delimiter` must be exactly one character and must not be `"`; otherwise raise `ValueError`.

Run the tests with `python -m pytest -q`.
