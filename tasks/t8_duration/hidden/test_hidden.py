import random

import pytest

from duration import format_duration, parse_duration


@pytest.mark.parametrize(
    "text,value",
    [
        ("1h30m", 5400),
        ("2w3d", 1468800),
        ("05m", 300),
        ("0s", 0),
        ("-1h", -3600),
        ("-0s", 0),
        ("1w1d1h1m1s", 604800 + 86400 + 3600 + 61),
        ("90s", 90),
        ("100h", 360000),
    ],
)
def test_parse_valid(text, value):
    assert parse_duration(text) == value


@pytest.mark.parametrize(
    "bad",
    ["", "30m1h", "1h1h", "10", "h", " 1h", "1h ", "1 h", "1H", "+1h", "--1h", "1h-30m",
     "1.5h", "-", "1hm", "1d2w", None, 5],
)
def test_parse_invalid(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)


@pytest.mark.parametrize(
    "value,text",
    [(5400, "1h30m"), (90061, "1d1h1m1s"), (0, "0s"), (-3600, "-1h"), (604800, "1w"),
     (59, "59s"), (-61, "-1m1s"), (1209600 + 1, "2w1s")],
)
def test_format(value, text):
    assert format_duration(value) == text


@pytest.mark.parametrize("bad", [1.0, "60", True, None])
def test_format_type_error(bad):
    with pytest.raises(TypeError):
        format_duration(bad)


def test_round_trip():
    rng = random.Random(3)
    for _ in range(2000):
        x = rng.randint(-10**8, 10**8)
        assert parse_duration(format_duration(x)) == x
