"""Reference solution (never shown to agents).

Any 7 consecutive days contain exactly 5 weekdays, so jumping w whole weeks
passes 5*w weekdays. Weekday holidays inside the jumped span were counted as
business days, so they are added back to the remaining steps.
"""

import bisect
import datetime

_DAY = datetime.timedelta(days=1)


def add_business_days(start, n, holidays=()):
    if not isinstance(start, datetime.date) or isinstance(start, datetime.datetime):
        raise TypeError("start must be a date")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    hol = {h for h in holidays if h.weekday() < 5}
    ordered = sorted(hol)

    def biz(d):
        return d.weekday() < 5 and d not in hol

    d = start
    if n == 0:
        while not biz(d):
            d += _DAY
        return d
    step = 1 if n > 0 else -1
    remaining = abs(n)
    while remaining > 10:
        # keep at least one step so the final date is found by stepping
        weeks = (remaining - 1) // 5
        target = d + datetime.timedelta(weeks=weeks * step)
        if step > 0:  # span (d, target]
            crossed = bisect.bisect_right(ordered, target) - bisect.bisect_right(ordered, d)
        else:  # span [target, d)
            crossed = bisect.bisect_left(ordered, d) - bisect.bisect_left(ordered, target)
        remaining = remaining - 5 * weeks + crossed
        d = target
    while remaining > 0:
        d += step * _DAY
        if biz(d):
            remaining -= 1
    return d
