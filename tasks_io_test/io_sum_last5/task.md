`program.py` must define `process_sequence(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list. Valid input is a list of integers.

Examples:
- `process_sequence([0, 8, 7, 7])` returns `[0, 8, 15, 22]`
- `process_sequence([3, 17, 2, 18, 13])` returns `[3, 20, 22, 40, 53]`
- `process_sequence([0, 2, 6])` returns `[0, 2, 8]`
- `process_sequence([16, 19, 0, 17, 6, 20])` returns `[16, 35, 35, 52, 58, 62]`
- `process_sequence([7, 14, 18, 8, 0, 5, 13, 10, 8])` returns `[7, 21, 39, 47, 47, 45, 44, 36, 36]`
- `process_sequence([6, 10, 3, 2, 12])` returns `[6, 16, 19, 21, 33]`
- `process_sequence([11, 11, 19, 8])` returns `[11, 22, 41, 49]`
- `process_sequence([14, 17, 3])` returns `[14, 31, 34]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
