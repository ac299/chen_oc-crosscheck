import time

import pytest

from globmatch import match

CASES = [
    ("src/**/*.py", "src/a/b/c.py", True),
    ("src/**/*.py", "src/c.py", True),
    ("src/**/*.py", "src/a/c.txt", False),
    ("*.py", "a/b.py", False),
    ("**", "", True),
    ("**", "a/b/c", True),
    ("**/x", "x", True),
    ("**/x", "a/b/x", True),
    ("**/x", "a/bx", False),
    ("a/**", "a", True),
    ("a/**", "a/b/c", True),
    ("a/**", "ab", False),
    ("a/**/b", "a/b", True),
    ("a/**/b", "a/x/y/b", True),
    ("a/**/b", "a/xb", False),
    ("a**b", "axxb", True),
    ("a**b", "ax/xb", False),
    ("?", "a", True),
    ("?", "/", False),
    ("?", "", False),
    ("a?c", "abc", True),
    ("*", "", True),
    ("*", "a/b", False),
    ("[abc]", "b", True),
    ("[a-c]x", "cx", True),
    ("[a-c]x", "dx", False),
    ("[!0-9]", "a", True),
    ("[!0-9]", "5", False),
    ("[^0-9]", "a", True),
    ("[]a]", "]", True),
    ("[]a]", "a", True),
    ("[!]a]", "]", False),
    ("[!]a]", "b", True),
    ("[-a]", "-", True),
    ("[a-]", "-", True),
    ("[a/b]", "/", False),
    ("[abc", "[abc", True),
    ("[abc", "a", False),
    ("\\*", "*", True),
    ("\\*", "a", False),
    ("\\?x", "?x", True),
    ("\\[a]", "[a]", True),
    ("a\\\\b", "a\\b", True),
    ("A*", "abc", False),
    (".*", ".hidden", True),
    ("*", ".hidden", True),
    ("a.b", "a.b", True),
    ("a.b", "axb", False),
    ("(x)+", "(x)+", True),
    ("a/*/c", "a/b/c", True),
    ("a/*/c", "a/c", False),
    ("a/*/c", "a/b/d/c", False),
]


@pytest.mark.parametrize("pattern,path,expected", CASES)
def test_cases(pattern, path, expected):
    assert match(pattern, path) is expected


def test_trailing_backslash_invalid():
    with pytest.raises(ValueError):
        match("abc\\", "abc")


def test_no_exponential_blowup():
    t0 = time.perf_counter()
    assert match("*a" * 20 + "b", "a" * 60) is False
    assert match("**/" * 15 + "z", "/".join("a" * 30)) is False
    assert time.perf_counter() - t0 < 1.0
