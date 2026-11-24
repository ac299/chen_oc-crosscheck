`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[int]. Task-specific input type: bit_seq, value range: (0, 2).

Examples:
- `process([0, 0, 0, 0])` returns `[0, 0, 0, 0]`
- `process([1, 0, 0, 0, 0, 0, 0, 0, 1, 0])` returns `[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- `process([1, 0, 0, 1, 1, 1, 0, 0])` returns `[0, 0, 0, 0, 0, 0, 0, 0]`
- `process([1, 0, 1, 0, 1, 0, 1, 1, 0, 0])` returns `[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- `process([0])` returns `[0]`
- `process([0, 0, 0, 1, 1])` returns `[0, 0, 0, 0, 0]`
- `process([1, 0, 1, 1, 0, 1, 0, 0])` returns `[0, 0, 0, 0, 0, 0, 0, 0]`
- `process([0, 0, 1, 1, 1, 0, 1, 0, 0])` returns `[0, 0, 0, 1, 0, 0, 0, 0, 0]`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
