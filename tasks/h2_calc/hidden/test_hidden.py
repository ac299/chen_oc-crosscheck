import random
import re
from fractions import Fraction

import pytest

from calc import evaluate


def oracle(expr, variables=None):
    """Python's own grammar with every literal and variable made exact."""
    env = {"F": Fraction}
    for k, v in (variables or {}).items():
        env[k] = Fraction(v)
    code = re.sub(r"\d+(?:\.\d+)?", lambda m: f"F('{m.group(0)}')", expr)
    r = eval(code, {"__builtins__": {}}, env)  # noqa: S307 - test oracle only
    return int(r) if r.denominator == 1 else r


@pytest.mark.parametrize(
    "expr",
    ["-2**2", "2**-1", "2**3**2", "(-2)**2", "-7 // 2", "-7 % 2", "7 % -3", "1/3 + 1/6",
     "2 * -3", "--4", "-+-4", "1.5 * 4", "10 / 4", "2 ** 10 // 3", "3 - 2 - 1", "64 / 4 / 2",
     "2 ** -2 ** 2", "-(3 - 5) ** 3", "1.25 % 0.5", "100 // 7 * 7 + 100 % 7"],
)
def test_matches_python_semantics(expr):
    got = evaluate(expr)
    exp = oracle(expr)
    assert got == exp and type(got) is type(exp), (expr, got, exp)


def test_return_types():
    assert type(evaluate("4 / 2")) is int
    assert evaluate("1 / 3") == Fraction(1, 3)
    assert isinstance(evaluate("1 / 3"), Fraction)


def test_variables():
    assert evaluate("x * y + z", {"x": 2, "y": Fraction(1, 2), "z": 3}) == 4
    assert evaluate("_a1 ** 2", {"_a1": -3}) == 9
    with pytest.raises(KeyError):
        evaluate("x + 1", {})
    with pytest.raises(KeyError):
        evaluate("x + 1")


def test_whitespace():
    assert evaluate(" \t1+\t2 ") == 3


@pytest.mark.parametrize("expr", ["1/0", "1 // 0", "5 % 0", "0 ** -1", "1 / (2 - 2)"])
def test_zero_division(expr):
    with pytest.raises(ZeroDivisionError):
        evaluate(expr)


@pytest.mark.parametrize("expr", ["2 ** 0.5", "2 ** (1/2)", "2 ** 1001", "2 ** -1001"])
def test_power_limits(expr):
    with pytest.raises(ValueError):
        evaluate(expr)


@pytest.mark.parametrize(
    "expr",
    ["", "   ", "(1 + 2", "1 + 2)", "1 2", "1 +", "* 2", "1.", ".5", "1 $ 2", "()", "2 *** 3",
     "1e5", "x y"],
)
def test_syntax_errors(expr):
    with pytest.raises(ValueError):
        evaluate(expr, {"x": 1, "y": 2})


def _rand_expr(rng, depth=0):
    if depth > 3 or rng.random() < 0.3:
        return str(rng.randint(0, 9)) if rng.random() < 0.8 else f"{rng.randint(0, 9)}.{rng.randint(1, 9)}"
    kind = rng.random()
    if kind < 0.15:
        return rng.choice(["-", "+"]) + _rand_expr(rng, depth + 1)
    if kind < 0.3:
        return "(" + _rand_expr(rng, depth + 1) + ")"
    if kind < 0.38:
        return f"({_rand_expr(rng, depth + 1)}) ** {rng.choice(['0', '1', '2', '3', '-1', '(-2)'])}"
    op = rng.choice(["+", "-", "*", "/", "//", "%", "+", "*"])
    return f"{_rand_expr(rng, depth + 1)} {op} {_rand_expr(rng, depth + 1)}"


def test_random_against_oracle():
    rng = random.Random(11)
    checked = 0
    while checked < 400:
        e = _rand_expr(rng)
        try:
            exp = oracle(e)
        except ZeroDivisionError:
            with pytest.raises(ZeroDivisionError):
                evaluate(e)
            continue
        assert evaluate(e) == exp, e
        checked += 1
