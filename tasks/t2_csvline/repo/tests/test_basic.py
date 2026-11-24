from csvline import parse_line


def test_simple():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_quoted_delimiter():
    assert parse_line('"a,b",c') == ["a,b", "c"]
