---
name: mirror-example-representation
description: "Use when the task text or docstring contains a concrete example, sample input, or literal output format that hidden tests will compare against"
---
## When to use
When the task description, docstring, or an inline example (e.g. `>>> data = [...]`, a sample input string, a sample output row) shows concrete values. Hidden tests usually compare against exactly that representation.

## Steps
1. Find every literal in the task text: sample inputs, sample outputs, printed examples, default argument values. Treat them as the specification, not as decoration.
2. For parsing, support the format the example actually shows. If the example uses a non-ISO layout, parse with `datetime.strptime` using that layout (or try several common layouts) instead of assuming ISO.
3. For output rows/records, reproduce the example's representation exactly: if the example shows a tuple, emit a tuple; if it shows a joined string, join; if it shows a dict keyed by name, key by name. Do not substitute a "cleaner" representation.
4. For container shapes, match the example's nesting: if the example indexes a result by predicate/column name, return a dict keyed that way rather than a positional list.
5. When the example is absent, prefer the simplest shape that satisfies the stated return type.

## Pitfalls
- Assuming ISO dates when the example shows another layout.
- Re-joining parsed fields into a string when the example shows the parsed tuple.
- Returning a list of booleans where the example indexes by name.
- Hardcoding a column name the example does not show.
