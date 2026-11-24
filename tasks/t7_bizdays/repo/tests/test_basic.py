from datetime import date

from bizdays import add_business_days


def test_simple_forward():
    # 2026-11-16 is a Monday
    assert add_business_days(date(2026, 11, 16), 1) == date(2026, 11, 17)
