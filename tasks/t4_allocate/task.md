The function `allocate(total, weights)` in `money.py` splits an integer amount of cents across recipients in proportion to `weights`. The current code loses or invents cents. Fix it so that it follows these rules.

- `total` is an int (it may be negative or zero). `weights` is a non-empty list of non-negative ints with a positive sum. Otherwise raise `ValueError`. `bool` values are not accepted as ints.
- The result is a list of ints with the same length as `weights` and `sum(result) == total` exactly.
- Use the largest-remainder method on `abs(total)`. Each share first gets `floor(abs(total) * w / W)` where `W = sum(weights)`. The leftover cents go one each to the shares with the largest fractional remainders. Ties are broken by the lower index. For a negative `total`, compute the split for `abs(total)` and negate every share.
- A recipient with weight 0 always gets 0.
- Use exact integer arithmetic. Do not use floats.

Run the tests with `python -m pytest -q`.
