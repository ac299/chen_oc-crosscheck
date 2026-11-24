`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[int]. Task-specific input type: int_list, value range: (1, 5).

Examples:
- `process([2, 2, 2, 1])` returns `8`
- `process([1, 5, 4, 1, 1, 1, 2, 2])` returns `80`
- `process([5, 1, 5, 2, 5, 4, 2, 4])` returns `8000`
- `process([1, 2, 4, 3])` returns `24`
- `process([2, 2, 3, 1])` returns `12`
- `process([3])` returns `3`
- `process([5, 3, 1, 4, 5])` returns `300`
- `process([5, 3, 5, 2])` returns `150`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
