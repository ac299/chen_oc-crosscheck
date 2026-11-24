import pytest

from roman import from_roman, to_roman


def test_round_trip_all():
    for n in range(1, 4000):
        assert from_roman(to_roman(n)) == n


def test_known_values():
    assert to_roman(3999) == "MMMCMXCIX"
    assert to_roman(4) == "IV"
    assert to_roman(40) == "XL"


@pytest.mark.parametrize("bad", [0, -1, 4000, 2.0, True, "5", None])
def test_to_roman_invalid(bad):
    with pytest.raises(ValueError):
        to_roman(bad)


@pytest.mark.parametrize(
    "bad",
    ["IIII", "VV", "IC", "IL", "XM", "MMMM", "IIV", "VX", "CMCM", "", " X", "x", "mcm",
     "XXXX", "LL", "DD", "CCCC", "IXI", "XCX", "VIV", "ABC", 10, None],
)
def test_from_roman_invalid(bad):
    with pytest.raises(ValueError):
        from_roman(bad)
