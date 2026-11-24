import time
from datetime import date, datetime, timedelta

import pytest

from bizdays import add_business_days

MON = date(2026, 11, 16)
FRI = date(2026, 11, 20)
SAT = date(2026, 11, 21)
SUN = date(2026, 11, 22)


def slow(start, n, holidays=()):
    hol = set(holidays)

    def biz(d):
        return d.weekday() < 5 and d not in hol

    d = start
    if n == 0:
        while not biz(d):
            d += timedelta(days=1)
        return d
    step = timedelta(days=1 if n > 0 else -1)
    for _ in range(abs(n)):
        d += step
        while not biz(d):
            d += step
    return d


def test_over_weekend():
    assert add_business_days(FRI, 1) == date(2026, 11, 23)
    assert add_business_days(MON, -1) == date(2026, 11, 13)


def test_from_weekend_start():
    assert add_business_days(SAT, 1) == date(2026, 11, 23)
    assert add_business_days(SUN, -1) == FRI
    assert add_business_days(SAT, -1) == FRI


def test_zero():
    assert add_business_days(MON, 0) == MON
    assert add_business_days(SAT, 0) == date(2026, 11, 23)
    assert add_business_days(FRI, 0, holidays=[FRI]) == date(2026, 11, 23)


def test_holidays():
    hol = [date(2026, 11, 17), date(2026, 11, 23)]
    assert add_business_days(MON, 1, hol) == date(2026, 11, 18)
    assert add_business_days(FRI, 1, hol) == date(2026, 11, 24)
    assert add_business_days(date(2026, 11, 24), -1, hol) == FRI


def test_holiday_on_weekend_ignored():
    assert add_business_days(FRI, 1, [SAT]) == date(2026, 11, 23)


def test_holidays_iterable_generator():
    assert add_business_days(MON, 1, (d for d in [date(2026, 11, 17)])) == date(2026, 11, 18)


def test_matches_slow_reference():
    hol = [date(2026, 12, 25), date(2027, 1, 1), date(2026, 12, 26), date(2027, 1, 18)]
    for offset in range(14):
        start = date(2026, 12, 14) + timedelta(days=offset)
        for n in list(range(-40, 41)) + [250, -250, 777]:
            assert add_business_days(start, n, hol) == slow(start, n, hol), (start, n)


def test_large_n_fast():
    t0 = time.perf_counter()
    res = add_business_days(MON, 500_000)
    assert time.perf_counter() - t0 < 1.0
    assert res == MON + timedelta(weeks=100_000)
    res2 = add_business_days(MON, -500_000)
    assert res2 == MON - timedelta(weeks=100_000)


@pytest.mark.parametrize("start,n", [(datetime(2026, 11, 16, 9), 1), ("2026-11-16", 1), (MON, 1.0), (MON, True)])
def test_type_errors(start, n):
    with pytest.raises(TypeError):
        add_business_days(start, n)
