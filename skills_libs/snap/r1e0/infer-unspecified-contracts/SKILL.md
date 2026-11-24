---
name: infer-unspecified-contracts
description: "Use when the task leaves input formats, column names, or exact return shapes unspecified and hidden tests will check them"
---
## When to use
When the task description does not fully pin down the data contract: input string formats, column names, the exact shape/type of the return value, or how content should be represented. Hidden tests will compare against a specific convention you must infer.

## Steps
1. Re-read the task text, docstring, and any inline example (e.g. `>>> data = [...]`) for concrete values. The example is the strongest signal of the expected format.
2. For input parsing, support the format shown in the example. If the example uses a non-ISO date layout, parse with `datetime.strptime` using that layout (or try several common layouts) rather than assuming ISO.
3. For column/field selection, do not hardcode a guessed name. Inspect the actual object at runtime: pick the column case-insensitively, or fall back to the first/last numeric column, and handle a DatetimeIndex vs positional index explicitly.
4. For return values, match the stated type exactly: if the spec says a dict, return a dict keyed by item; if it says a list of tuples, return tuples, not joined strings. Mirror the example's representation.
5. When comparing arrays/DataFrames, reproduce the documented transformation exactly (e.g. same dtype, same rounding) instead of an approximation.

## Pitfalls
- Assuming ISO format when the example shows another layout.
- Hardcoding a column name that the tests do not use.
- Returning a list where the spec says dict, or strings where it says tuples.
- Casting a datetime index to float or otherwise losing index type.
