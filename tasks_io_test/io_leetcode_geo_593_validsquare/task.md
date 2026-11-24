`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[list[int]]. Task-specific input type: points_list, value range: (-20, 20).

Examples:
- `process([[-13, -19], [-3, -5], [-6, -12], [-14, 14], [-15, 17], [7, -18], [-19, -15]])` returns `false`
- `process([[-6, 12], [18, -19], [15, -8]])` returns `false`
- `process([[14, 6], [-6, 8], [17, -3], [-20, -10], [7, 1], [-3, -11], [-7, 1]])` returns `false`
- `process([[-15, 4], [-14, 2]])` returns `false`
- `process([[18, -4], [-18, 9], [14, -13], [4, -15]])` returns `false`
- `process([[-2, 20], [19, 3], [16, -8], [-16, -18], [-6, -2], [-15, -6]])` returns `false`
- `process([[4, -3], [9, 20]])` returns `false`
- `process([[-10, 3], [2, -7], [-3, -16], [18, 20]])` returns `false`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
