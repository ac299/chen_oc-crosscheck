`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([-10, -2, -3, -3])` returns `[10, -8, 1, 0]`
- `process_sequence([-7, 7, -8, 8, 3])` returns `[7, 0, 1, 0, -5]`
- `process_sequence([-10, -8, -4])` returns `[10, -2, -4]`
- `process_sequence([6, 9, -10, 7, -4, 10])` returns `[6, 3, 1, -3, -3, 6]`
- `process_sequence([-3, 4, 8, -2, -10, -5, 3, 0, -2])` returns `[3, 1, 4, -6, 8, -5, -2, -3, 2]`
- `process_sequence([-4, 0, -7, -8, 2])` returns `[4, -4, 7, 1, -6]`
- `process_sequence([1, 1, 9, -2])` returns `[1, 0, 8, -7]`
- `process_sequence([4, 7, -7])` returns `[4, 3, 0]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
