`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([-19, -3, -5, -6])` returns `[19, 3, 5, 6]`
- `process_sequence([-14, 14, -15, 17, 7])` returns `[14, 14, 15, 17, 7]`
- `process_sequence([-19, -15, -7])` returns `[19, 15, 7]`
- `process_sequence([12, 18, -19, 15, -8, 14])` returns `[12, 18, 19, 15, 8, 14]`
- `process_sequence([-6, 8, 17, -3, -20, -10, 7, 1, -3])` returns `[6, 8, 17, 3, 20, 10, 7, 1, 3]`
- `process_sequence([-7, 1, -14, -15, 4])` returns `[7, 1, 14, 15, 4]`
- `process_sequence([2, 2, 18, -4])` returns `[2, 2, 18, 4]`
- `process_sequence([9, 14, -13])` returns `[9, 14, 13]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
