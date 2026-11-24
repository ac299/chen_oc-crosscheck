`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: tuple/list with 2 numbers. Task-specific input type: pair, value range: (1, 100).

Examples:
- `process([82, 15])` returns `1`
- `process([4, 95])` returns `1`
- `process([36, 32])` returns `4`
- `process([29, 18])` returns `1`
- `process([95, 14])` returns `1`
- `process([87, 95])` returns `1`
- `process([70, 12])` returns `2`
- `process([76, 55])` returns `1`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
