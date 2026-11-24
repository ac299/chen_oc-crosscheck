Implement `next_fire(expr, after)` in `cron.py`. It returns the first `datetime` strictly later than `after` that matches the five-field cron expression `expr`.

Fields, separated by single spaces, in this order:

| field | allowed values |
| --- | --- |
| minute | 0-59 |
| hour | 0-23 |
| day of month | 1-31 |
| month | 1-12 |
| day of week | 0-7, where both 0 and 7 mean Sunday and 1 is Monday |

Each field is a comma-separated list of items. An item is `*`, a number `N`, a range `A-B` (inclusive, `A <= B`), or any of those followed by a step `/S` with `S >= 1` (`*/15`, `10-30/5`, `5/20`). `N/S` means "from N to the field's maximum, every S".

Day matching follows classic cron: if both the day-of-month and the day-of-week fields are restricted (neither is exactly `*`), a date matches when **either** field matches. If one of them is `*`, only the other one is checked. A field written as `*/1` or `*/S` counts as restricted.

Other rules:
- `after` is a naive `datetime`. Seconds and microseconds of `after` are ignored except that the result must be strictly later than `after`; the result always has second and microsecond 0.
- Raise `ValueError` for malformed expressions: wrong field count, values out of range, `A > B`, a step of 0, empty items, extra spaces, or any other character.
- If no matching time exists within the next 5 years (for example `0 0 30 2 *`), raise `ValueError`.
- It must be fast: computing `next_fire("0 0 29 2 1", datetime(2026, 1, 1))` must not step minute by minute through years.

Run the tests with `python -m pytest -q`.
