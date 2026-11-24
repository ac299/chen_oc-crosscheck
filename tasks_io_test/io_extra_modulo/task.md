`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: tuple/list with 2 numbers. Task-specific input type: pair, value range: (1, 50).

Examples:
- `process([41, 8])` returns `1`
- `process([2, 48])` returns `2`
- `process([18, 16])` returns `2`
- `process([15, 9])` returns `6`
- `process([48, 7])` returns `6`
- `process([44, 48])` returns `44`
- `process([35, 6])` returns `5`
- `process([38, 28])` returns `10`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
