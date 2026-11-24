`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([1, 47, 17, 15])` returns `[1, 47, 47, 47]`
- `process_sequence([8, 47, 6, 43, 47, 34])` returns `[8, 47, 47, 47, 47, 47]`
- `process_sequence([37, 27, 2, 1])` returns `[37, 37, 37, 37]`
- `process_sequence([13, 14, 32, 38])` returns `[13, 14, 32, 38]`
- `process_sequence([35, 12, 45])` returns `[35, 35, 45]`
- `process_sequence([14, 28, 37, 17, 0, 48, 10, 44, 27])` returns `[14, 28, 37, 37, 37, 48, 48, 48, 48]`
- `process_sequence([17, 9, 13, 48, 21, 6, 5, 24])` returns `[17, 17, 17, 48, 48, 48, 48, 48]`
- `process_sequence([22, 22, 38, 16])` returns `[22, 22, 38, 38]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
