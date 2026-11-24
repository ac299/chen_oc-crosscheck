`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([-5, -1, -2, -2])` returns `[-5, -6, -8, -10]`
- `process_sequence([-4, 5, 3, -4, 4])` returns `[-4, 1, 4, 0, 4]`
- `process_sequence([-5, -5, -4, -2, -2, 3, 4, -5, 3])` returns `[-5, -10, -14, -16, -18, -15, -11, -16, -13]`
- `process_sequence([5, 3, 1, -2, 2, 4])` returns `[5, 8, 9, 7, 9, 13]`
- `process_sequence([-5, -3, 1, 0, -1, -3, -2])` returns `[-5, -8, -7, -7, -8, -11, -13]`
- `process_sequence([-4, -4, 1, -4, 0, 0, 4, -1])` returns `[-4, -8, -7, -11, -11, -11, -7, -8]`
- `process_sequence([2, 3, -4])` returns `[2, 5, 1]`
- `process_sequence([-4, 3, -1, 5, 4, 0, 4, -2, -4])` returns `[-4, -1, -2, 3, 7, 7, 11, 9, 5]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
