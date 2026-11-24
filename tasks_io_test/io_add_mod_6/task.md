`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([0, 5, 2, 1])` returns `[0, 5, 1, 2]`
- `process_sequence([1, 5, 0, 5, 5, 4])` returns `[1, 0, 0, 5, 4, 2]`
- `process_sequence([4, 3, 0, 0])` returns `[4, 1, 1, 1]`
- `process_sequence([1, 1, 4, 4])` returns `[1, 2, 0, 4]`
- `process_sequence([4, 1, 5])` returns `[4, 5, 4]`
- `process_sequence([1, 3, 4, 2, 6, 6, 0, 6, 6])` returns `[1, 4, 2, 4, 4, 4, 4, 4, 4]`
- `process_sequence([5, 3, 2, 2, 1])` returns `[5, 2, 4, 0, 1]`
- `process_sequence([6, 2, 0, 0, 3, 0])` returns `[0, 2, 2, 2, 5, 5]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
