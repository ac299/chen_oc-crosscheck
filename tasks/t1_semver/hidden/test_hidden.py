import pytest

from semver import compare, parse

CHAIN = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


def test_spec_precedence_chain():
    for i, a in enumerate(CHAIN):
        for j, b in enumerate(CHAIN):
            assert compare(a, b) == (i > j) - (i < j), (a, b)


def test_numeric_identifiers_compare_numerically():
    assert compare("1.0.0-alpha.10", "1.0.0-alpha.2") == 1
    assert compare("1.0.0-2", "1.0.0-10") == -1


def test_numeric_lower_than_alphanumeric():
    assert compare("1.0.0-1", "1.0.0-a") == -1
    assert compare("1.0.0-alpha.a", "1.0.0-alpha.1") == 1


def test_build_metadata_ignored():
    assert compare("1.0.0+a", "1.0.0+b") == 0
    assert compare("1.0.0-rc.1+build.5", "1.0.0-rc.1") == 0


def test_parse_fields():
    assert parse("1.2.3-rc.1+build.007") == (1, 2, 3, ("rc", "1"), ("build", "007"))


@pytest.mark.parametrize(
    "bad",
    [
        "01.0.0",
        "1.02.0",
        "1.0.03",
        "1.0.0-",
        "1.0.0+",
        "1.0.0-alpha..1",
        "1.0.0-01",
        " 1.0.0",
        "1.0.0\n",
        "1.0",
        "1.0.0-al$pha",
        "",
    ],
)
def test_invalid_versions(bad):
    with pytest.raises(ValueError):
        parse(bad)


@pytest.mark.parametrize("ok", ["0.0.0", "1.0.0-0", "1.0.0-0a", "1.0.0+001", "1.0.0-x-y-z.--"])
def test_valid_versions(ok):
    parse(ok)
