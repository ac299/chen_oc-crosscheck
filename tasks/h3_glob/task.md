Implement `match(pattern, path)` in `globmatch.py`. It returns `True` when the `/`-separated `path` matches the glob `pattern`. Do not use `fnmatch`, `glob`, `pathlib` matching or `re` translation helpers from the standard library; regular expressions you build yourself are fine.

Pattern syntax:
- `?` matches exactly one character other than `/`.
- `*` matches any run (possibly empty) of characters other than `/`.
- `**` is only special when it forms a whole path segment (`**`, `a/**`, `**/b`, `a/**/b`). It then matches zero or more whole segments. A `**` inside a segment such as `a**b` behaves like two `*`.
- `[...]` is a character class matching one character other than `/`: lists (`[abc]`), ranges (`[a-z]`), negation with a leading `!` or `^` (`[!0-9]`). A `]` placed first (after an optional negation mark) is a literal (`[]a]`). A `-` placed first or last is a literal. A `[` without a closing `]` is a literal `[`.
- `\` escapes the next character, making it literal (`\*`, `\?`, `\[`, `\\`). A trailing lone `\` makes the pattern invalid: raise `ValueError`.
- Every other character matches itself. Matching is case-sensitive and must cover the whole path.
- Leading dots are not special.

Examples: `match("src/**/*.py", "src/a/b/c.py")` and `match("src/**/*.py", "src/c.py")` are `True`; `match("*.py", "a/b.py")` is `False`; `match("**", "")` is `True`.

Matching must not take exponential time: patterns like `"*a" * 20 + "b"` against `"a" * 60` must return quickly.

Run the tests with `python -m pytest -q`.
