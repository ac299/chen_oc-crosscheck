---
name: unclear-input-format
description: "Load this when the task does not fully specify the input format (column names, keys, index, dtypes)."
---
## When to use
The task description or docstring does not state exactly how the input is structured.

## Steps
1. Collect every hint about the input: the docstring, parameter names, examples, error-handling rules.
2. Use the names the task itself mentions. Do not invent default names.
3. If something stays unspecified, write code that does not depend on it, and say so in your summary.

## Pitfalls
- Assuming a column is the index, or that a column has a conventional name.
