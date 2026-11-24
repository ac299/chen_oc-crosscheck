from semver import compare, parse


def test_core_order():
    assert compare("1.2.3", "1.10.0") == -1
    assert compare("2.0.0", "1.9.9") == 1
    assert compare("1.0.0", "1.0.0") == 0


def test_prerelease_below_release():
    assert compare("1.0.0-alpha", "1.0.0") == -1


def test_parse_basic():
    assert parse("1.2.3") == (1, 2, 3, (), ())
