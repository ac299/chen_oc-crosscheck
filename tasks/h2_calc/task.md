Implement `evaluate(expr, variables=None)` in `calc.py`: an exact arithmetic expression evaluator. Do not use `eval`, `exec`, `compile` or the `ast` module.

Syntax:
- Numbers: decimal integers (`42`) or decimals with digits on both sides of the point (`1.25`). No exponent notation, no leading `+`/`-` as part of the literal (signs are operators).
- Variables: names matching `[A-Za-z_][A-Za-z0-9_]*`, looked up in `variables` (a dict of name to int or `fractions.Fraction`).
- Operators, from lowest to highest precedence: `+` `-` (binary, left-associative); `*` `/` `//` `%` (left-associative); unary `+` `-`; `**` (right-associative). Parentheses group.
- Precedence and associativity follow Python exactly, including that `**` binds tighter than a unary minus on its left (`-2**2` is `-4`) but its right operand may carry a unary sign (`2**-1` is `1/2`).
- Spaces and tabs between tokens are ignored.

Semantics:
- All arithmetic is exact using `fractions.Fraction`. `/` is true division. `//` and `%` follow Python's floor semantics for Fractions (`-7 // 2 == -4`, `-7 % 2 == 1`).
- `a ** b` requires `b` to be an integer value (raise `ValueError` otherwise) with `abs(b) <= 1000` (raise `ValueError` otherwise). `0 ** -1` raises `ZeroDivisionError`.
- Division, floor division or modulo by zero raises `ZeroDivisionError`.
- An unknown variable raises `KeyError`. Any syntax error (empty input, unbalanced parentheses, two operands in a row, a trailing operator, `1.`, `.5`, unknown characters) raises `ValueError`.
- Return an `int` when the result is a whole number, otherwise a `Fraction`.

Run the tests with `python -m pytest -q`.
