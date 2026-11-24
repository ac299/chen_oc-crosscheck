`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([0, 2, 1, 1])` returns `[0, 2, 3, 0]`
- `process_sequence([0, 4, 0, 4, 3])` returns `[0, 0, 0, 0, 3]`
- `process_sequence([0, 0, 1])` returns `[0, 0, 1]`
- `process_sequence([4, 4, 0, 4, 1, 4])` returns `[0, 0, 0, 0, 1, 1]`
- `process_sequence([1, 3, 4, 2, 0, 1, 3, 2, 2])` returns `[1, 0, 0, 2, 2, 3, 2, 0, 2]`
- `process_sequence([1, 2, 0, 0, 3])` returns `[1, 3, 3, 3, 2]`
- `process_sequence([2, 2, 4, 2])` returns `[2, 0, 0, 2]`
- `process_sequence([3, 4, 0])` returns `[3, 3, 3]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
