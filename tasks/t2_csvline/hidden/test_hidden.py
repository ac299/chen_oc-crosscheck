import pytest

from csvline import parse_line


def test_empty_line():
    assert parse_line("") == [""]


def test_trailing_and_empty_fields():
    assert parse_line("a,") == ["a", ""]
    assert parse_line(",,") == ["", "", ""]
    assert parse_line('"",x') == ["", "x"]


def test_whitespace_kept():
    assert parse_line(" a , b ") == [" a ", " b "]


def test_escaped_quotes():
    assert parse_line('"he said ""hi""",2') == ['he said "hi"', "2"]
    assert parse_line('""""') == ['"']


def test_quote_in_unquoted_field():
    assert parse_line('ab"c,d') == ['ab"c', "d"]


def test_line_endings_removed():
    assert parse_line("a,b\n") == ["a", "b"]
    assert parse_line("a,b\r\n") == ["a", "b"]
    assert parse_line('"x,y"\r\n') == ["x,y"]


def test_custom_delimiter():
    assert parse_line('a;"b;c";d', delimiter=";") == ["a", "b;c", "d"]
    assert parse_line("a,b", delimiter=";") == ["a,b"]


@pytest.mark.parametrize("bad", ['"abc', '"a"b,c', '"a" ,b', 'x,"unterminated'])
def test_malformed(bad):
    with pytest.raises(ValueError):
        parse_line(bad)


@pytest.mark.parametrize("delim", ["", ";;", '"'])
def test_bad_delimiter(delim):
    with pytest.raises(ValueError):
        parse_line("a", delimiter=delim)
