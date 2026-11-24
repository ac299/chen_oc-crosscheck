`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: int. Task-specific input type: single_int, value range: (0, 20).

Examples:
- `process(13)` returns `233`
- `process(16)` returns `987`
- `process(14)` returns `377`
- `process(5)` returns `5`
- `process(11)` returns `89`
- `process(9)` returns `34`
- `process(13)` returns `233`
- `process(16)` returns `987`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
