import time
from datetime import datetime, timedelta

import pytest

from cron import next_fire

D = datetime


def test_strictly_after_and_seconds():
    assert next_fire("* * * * *", D(2026, 1, 1, 10, 0, 30)) == D(2026, 1, 1, 10, 1)
    assert next_fire("0 10 * * *", D(2026, 1, 1, 10, 0)) == D(2026, 1, 2, 10, 0)
    assert next_fire("0 10 * * *", D(2026, 1, 1, 9, 59, 59, 999)) == D(2026, 1, 1, 10, 0)


def test_steps_and_ranges():
    assert next_fire("*/15 * * * *", D(2026, 1, 1, 10, 46)) == D(2026, 1, 1, 11, 0)
    assert next_fire("10-30/10 * * * *", D(2026, 1, 1, 10, 25)) == D(2026, 1, 1, 10, 30)
    assert next_fire("10-30/10 * * * *", D(2026, 1, 1, 10, 31)) == D(2026, 1, 1, 11, 10)
    assert next_fire("5/20 * * * *", D(2026, 1, 1, 10, 46)) == D(2026, 1, 1, 11, 5)
    assert next_fire("0 0,12 * * *", D(2026, 1, 1, 1, 0)) == D(2026, 1, 1, 12, 0)


def test_month_rollover_and_year():
    assert next_fire("0 0 1 * *", D(2026, 12, 15)) == D(2027, 1, 1)
    assert next_fire("0 0 31 * *", D(2026, 4, 1)) == D(2026, 5, 31)


def test_dow_sunday_zero_and_seven():
    # 2026-11-22 is a Sunday
    assert next_fire("0 8 * * 0", D(2026, 11, 20)) == D(2026, 11, 22, 8, 0)
    assert next_fire("0 8 * * 7", D(2026, 11, 20)) == D(2026, 11, 22, 8, 0)
    assert next_fire("0 8 * * 1-5", D(2026, 11, 21)) == D(2026, 11, 23, 8, 0)


def test_dom_dow_or_rule():
    # restricted both: 13th OR Friday. 2026-11-20 is Friday.
    assert next_fire("0 0 13 * 5", D(2026, 11, 14)) == D(2026, 11, 20)
    assert next_fire("0 0 13 * 5", D(2026, 11, 28)) == D(2026, 12, 4)
    # dom '*' -> only dow
    assert next_fire("0 0 * * 5", D(2026, 11, 14)) == D(2026, 11, 20)
    # dow '*' -> only dom
    assert next_fire("0 0 13 * *", D(2026, 11, 14)) == D(2026, 12, 13)


def test_star_step_counts_as_restricted():
    # dom */1 is restricted, so OR with dow 5 means every day matches
    assert next_fire("0 0 */1 * 5", D(2026, 11, 14, 1)) == D(2026, 11, 15)
    # dom */10 = 1,11,21,31 OR Friday
    assert next_fire("0 0 */10 * 5", D(2026, 11, 14)) == D(2026, 11, 20)


def test_leap_day_fast():
    t0 = time.perf_counter()
    assert next_fire("0 0 29 2 *", D(2026, 3, 1)) == D(2028, 2, 29)
    # month is February only: 29 Feb OR a Monday in February -> 2026-02-02
    assert next_fire("0 0 29 2 1", D(2026, 1, 1)) == D(2026, 2, 2)
    assert time.perf_counter() - t0 < 1.0


def test_impossible_raises():
    with pytest.raises(ValueError):
        next_fire("0 0 30 2 *", D(2026, 1, 1))
    with pytest.raises(ValueError):
        next_fire("0 0 31 4 *", D(2026, 1, 1))


@pytest.mark.parametrize(
    "bad",
    ["* * * *", "* * * * * *", "60 * * * *", "* 24 * * *", "* * 0 * *", "* * * 13 *", "* * * * 8",
     "5-1 * * * *", "*/0 * * * *", "1,,2 * * * *", "*  * * * *", " * * * * *", "a * * * *",
     "1-2-3 * * * *", "*/ * * * *", "-1 * * * *"],
)
def test_malformed(bad):
    with pytest.raises(ValueError):
        next_fire(bad, D(2026, 1, 1))


def brute(expr, after):
    from cron import next_fire as nf  # noqa: F401
    m, h, dom, mon, dow = expr.split()

    def expand(field, lo, hi):
        out = set()
        for item in field.split(","):
            step = 1
            has_step = "/" in item
            if has_step:
                item, s = item.split("/")
                step = int(s)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = map(int, item.split("-"))
            else:
                a = int(item)
                b = hi if has_step else a
            out.update(range(a, b + 1, step))
        return out

    M, H, DM, MO = expand(m, 0, 59), expand(h, 0, 23), expand(dom, 1, 31), expand(mon, 1, 12)
    DW = {d % 7 for d in expand(dow, 0, 7)}
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 400):
        cd = (t.isoweekday() % 7) in DW
        cm = t.day in DM
        if dom != "*" and dow != "*":
            day_ok = cd or cm
        elif dom != "*":
            day_ok = cm
        elif dow != "*":
            day_ok = cd
        else:
            day_ok = True
        if t.minute in M and t.hour in H and t.month in MO and day_ok:
            return t
        t += timedelta(minutes=1)
    raise AssertionError("brute force found nothing")


@pytest.mark.parametrize(
    "expr",
    ["7 3 * * 2", "0 */6 1,15 * *", "45 23 * 2 0", "0 12 1-7 * 1", "15 4 10-20/5 3-5 3,6", "0 0 31 * 1"],
)
def test_against_brute_force(expr):
    after = D(2026, 1, 30, 22, 17)
    for _ in range(4):
        got = next_fire(expr, after)
        assert got == brute(expr, after), (expr, after)
        after = got
