`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[int]. Task-specific input type: int_list, value range: (0, 20).

Examples:
- `process([7, 7, 4, 3])` returns `[3, 4, 7, 7]`
- `process([2, 18, 13, 1, 0, 2, 6, 7])` returns `[7, 6, 2, 0, 1, 13, 18, 2]`
- `process([19, 0, 17, 6, 20, 17, 13, 7])` returns `[7, 13, 17, 20, 6, 17, 0, 19]`
- `process([18, 8, 0, 5, 13, 10, 8])` returns `[8, 10, 13, 5, 0, 8, 18]`
- `process([6, 10])` returns `[10, 6]`
- `process([2])` returns `[2]`
- `process([3, 11, 11, 19, 8, 1])` returns `[1, 8, 19, 11, 11, 3]`
- `process([17, 3, 12, 2, 17, 9, 20])` returns `[20, 9, 17, 2, 12, 3, 17]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
