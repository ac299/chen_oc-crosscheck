"""Reference solution (never shown to agents). Recursive descent, Python grammar:

expr   := term (('+'|'-') term)*
term   := factor (('*'|'/'|'//'|'%') factor)*
factor := ('+'|'-') factor | power
power  := atom ('**' factor)?
"""

import re
from fractions import Fraction

_TOKEN = re.compile(r"\s*(?:(\d+\.\d+|\d+)|([A-Za-z_][A-Za-z0-9_]*)|(\*\*|//|[-+*/%()]))")


def _tokens(expr):
    pos, out = 0, []
    expr = expr.rstrip(" \t")
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f"bad character at {pos}")
        num, name, op = m.groups()
        nxt = expr[m.end():m.end() + 1]
        if num is not None and (nxt == "." or nxt.isalpha() or nxt == "_"):
            raise ValueError("malformed number")
        if num is not None:
            out.append(("num", Fraction(num)))
        elif name is not None:
            out.append(("name", name))
        else:
            out.append(("op", op))
        pos = m.end()
    for ch in expr:
        if ch not in " \t" and not (ch.isalnum() or ch in "_.+-*/%()"):
            raise ValueError("bad character")
    return out


class _Parser:
    def __init__(self, toks, variables):
        self.t, self.i, self.v = toks, 0, variables

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, op=None):
        tok = self.peek()
        if tok[0] is None or (op is not None and tok != ("op", op)):
            raise ValueError("unexpected token")
        self.i += 1
        return tok

    def expr(self):
        val = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            rhs = self.term()
            val = val + rhs if op == "+" else val - rhs
        return val

    def term(self):
        val = self.factor()
        while self.peek() in (("op", "*"), ("op", "/"), ("op", "//"), ("op", "%")):
            op = self.take()[1]
            rhs = self.factor()
            if op == "*":
                val = val * rhs
            else:
                if rhs == 0:
                    raise ZeroDivisionError("division by zero")
                val = val / rhs if op == "/" else (val // rhs if op == "//" else val % rhs)
        return val

    def factor(self):
        if self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            val = self.factor()
            return val if op == "+" else -val
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == ("op", "**"):
            self.take()
            exp = self.factor()
            if exp.denominator != 1:
                raise ValueError("non-integer exponent")
            if abs(exp) > 1000:
                raise ValueError("exponent too large")
            if base == 0 and exp < 0:
                raise ZeroDivisionError("zero to a negative power")
            return Fraction(base) ** int(exp)
        return base

    def atom(self):
        kind, val = self.peek()
        if kind == "num":
            self.i += 1
            return val
        if kind == "name":
            self.i += 1
            return Fraction(self.v[val])
        if (kind, val) == ("op", "("):
            self.take()
            inner = self.expr()
            self.take(")")
            return inner
        raise ValueError("expected a value")


def evaluate(expr, variables=None):
    toks = _tokens(expr)
    if not toks:
        raise ValueError("empty expression")
    p = _Parser(toks, variables or {})
    val = p.expr()
    if p.i != len(toks):
        raise ValueError("unexpected trailing input")
    return int(val) if val.denominator == 1 else val
