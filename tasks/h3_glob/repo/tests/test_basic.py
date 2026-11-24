from globmatch import match


def test_star():
    assert match("*.py", "a.py")
    assert not match("*.py", "a.txt")
