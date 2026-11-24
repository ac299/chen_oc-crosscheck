`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[int]. Task-specific input type: rpn_seq, value range: (0, 10).

Examples:
- `process([0, 4, 10, 1])` returns `[0, 4, 4, 1]`
- `process([9, 6, 10, 3, 10])` returns `[9, 6, 15, 3, 18]`
- `process([8, 6, 10, 0, 2, 5, 10])` returns `[8, 6, 14, 0, 2, 5, 7]`
- `process([1, 1, 5, 9, 10, 8, 10, 10])` returns `[1, 1, 5, 9, 14, 8, 22, 23]`
- `process([9, 3, 0, 4, 3, 6, 10, 10, 10])` returns `[9, 3, 0, 4, 3, 6, 9, 13, 13]`
- `process([9, 2, 3, 10, 10])` returns `[9, 2, 3, 5, 14]`
- `process([0, 3, 5, 1, 10, 10, 7, 10, 10])` returns `[0, 3, 5, 1, 6, 9, 7, 16, 16]`
- `process([9, 6, 2, 1, 1, 10, 6, 6, 7, 10])` returns `[9, 6, 2, 1, 1, 2, 6, 6, 7, 13]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
