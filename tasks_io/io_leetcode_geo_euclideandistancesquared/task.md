`program.py` must define `process(input_data)`, a function whose behaviour is only known from the examples below. Infer the rule and implement it so that it generalises to new inputs of the same kind, not just these examples.

Input: list[list[int]]. Task-specific input type: point_pair, value range: (-20, 20).

Examples:
- `process([[20, -13], [-19, -3]])` returns `1621`
- `process([[-5, -6], [-12, -14]])` returns `113`
- `process([[14, -15], [17, 7]])` returns `493`
- `process([[-18, -19], [-15, -7]])` returns `153`
- `process([[-6, 12], [18, -19]])` returns `1537`
- `process([[15, -8], [14, 6]])` returns `197`
- `process([[-6, 8], [17, -3]])` returns `650`
- `process([[-20, -10], [7, 1]])` returns `850`

The examples are also in `tests/test_basic.py`. Run the tests with `python -m pytest -q`.
