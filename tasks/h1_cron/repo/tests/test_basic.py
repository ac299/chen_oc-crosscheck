from datetime import datetime

from cron import next_fire


def test_every_minute():
    assert next_fire("* * * * *", datetime(2026, 1, 1, 10, 0)) == datetime(2026, 1, 1, 10, 1)


def test_daily():
    assert next_fire("30 9 * * *", datetime(2026, 1, 1, 10, 0)) == datetime(2026, 1, 2, 9, 30)
