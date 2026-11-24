---
name: task-checklist
description: "Use at the start of every task, before writing code: how to write and then check a short checklist of this task's own requirements"
---
## When to use
Any task: implement one function from a prose spec, no tests given. Read the spec once, extract every concrete claim, then verify each claim by running code.

## Build the checklist
Before coding, write a short numbered checklist in your reply (not in a file). Pull items only from what the spec states:
- Signature/imports: keep them exactly; body only.
- Return type/shape: scalar, tuple order, DataFrame columns/index names, list element type, Axes vs Figure.
- Exceptions: only those named, raised exactly when the stated condition holds; check order if several could apply.
- Edge cases explicitly mentioned (empty input, single element, missing file, defaults).
- Formats shown in examples: exact strings, column labels, index labels, rounding, NaN vs 0.
- Side effects: files created/deleted, warnings, plots, subprocess behavior.
- Defaults: default args and module constants must be honored.

## Check it
Write a throwaway script (outside the repo or delete after) that imports the function and asserts each checklist item: type checks, `list(df.columns)`, `df.index.tolist()`, tuple unpacking, `pytest.raises`-style try/except for each named exception, and the documented edge inputs. For plots assert `isinstance(result, Axes)`; for files assert existence then clean up. Run it, fix failures, rerun. Also run any provided tests.

## Pitfalls
- Don't invent exceptions or messages the spec didn't name; don't swallow named ones.
- Match example output literally (labels, spacing, NaN).
- Respect stated ordering of tuple returns and list contents.
- Close files/plots; avoid leaving temp artifacts in the repo.
- Don't change signature, imports, or constants; don't edit tests.
