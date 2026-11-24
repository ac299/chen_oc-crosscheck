"""Reference solution (never shown to agents)."""

import calendar
import re
from datetime import datetime, timedelta

_ITEM = re.compile(r"(\*|\d+|\d+-\d+)(?:/(\d+))?")
_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


def _field(text, lo, hi):
    values = set()
    for item in text.split(","):
        m = _ITEM.fullmatch(item)
        if not m:
            raise ValueError(f"bad item {item!r}")
        base, step = m.group(1), m.group(2)
        step = int(step) if step is not None else 1
        if step < 1:
            raise ValueError("step must be >= 1")
        if base == "*":
            a, b = lo, hi
        elif "-" in base:
            a, b = map(int, base.split("-"))
            if a > b:
                raise ValueError("range start after end")
        else:
            a = int(base)
            b = hi if m.group(2) is not None else a
        if a < lo or b > hi:
            raise ValueError("value out of range")
        values.update(range(a, b + 1, step))
    return values


def _parse(expr):
    if not isinstance(expr, str):
        raise ValueError("expression must be a string")
    parts = expr.split(" ")
    if len(parts) != 5 or any(p == "" for p in parts):
        raise ValueError("expected five fields")
    sets = [_field(p, lo, hi) for p, (lo, hi) in zip(parts, _RANGES)]
    sets[4] = {d % 7 for d in sets[4]}
    return sets, parts[2] != "*", parts[4] != "*"


def next_fire(expr, after):
    (mins, hours, doms, months, dows), dom_r, dow_r = _parse(expr)

    def day_ok(d):
        in_dom = d.day in doms
        in_dow = (d.isoweekday() % 7) in dows
        if dom_r and dow_r:
            return in_dom or in_dow
        if dom_r:
            return in_dom
        if dow_r:
            return in_dow
        return True

    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = start.date()
    limit = day.replace(year=day.year + 5) if not (day.month == 2 and day.day == 29) else day.replace(year=day.year + 5, day=28)
    first = True
    while day <= limit:
        if day.month in months and day_ok(day):
            for h in sorted(hours):
                for m in sorted(mins):
                    cand = datetime(day.year, day.month, day.day, h, m)
                    if cand >= start:
                        return cand
        if first:
            first = False
        if day.month not in months:
            # jump to first day of next month
            y, mo = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
            day = day.replace(year=y, month=mo, day=1)
            continue
        day += timedelta(days=1)
    raise ValueError("no matching time within five years")


_ = calendar  # kept for readers who want month lengths
