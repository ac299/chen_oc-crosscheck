`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[int]. Task-specific input type: int_list, value range: (-5, 10).

Examples:
- `process([2, 2, -1, -2])` returns `false`
- `process([-3, 8, -4, -5, -3, 1, 2, -5])` returns `false`
- `process([1, 8, 2, 9, 3, -5, 0, 8])` returns `false`
- `process([3, -1, 1, 5, -2])` returns `false`
- `process([7])` returns `true`
- `process([6])` returns `true`
- `process([3, -4, 9, -2, 7])` returns `false`
- `process([4])` returns `true`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
