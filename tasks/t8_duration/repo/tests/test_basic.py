from duration import format_duration, parse_duration


def test_examples():
    assert parse_duration("1h30m") == 5400
    assert format_duration(5400) == "1h30m"
