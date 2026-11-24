---
name: infer-io-contract
description: "Use when the task specifies a return type or input format only loosely (e.g. 'a dict', 'a DataFrame', 'a list of strings', timestamps, column names) and hidden tests will check exact structure."
---
## When to use
When the task description names a return type or input format but does not pin down the exact structure, field names, or string format (e.g. "returns a dict", "a DataFrame", "a list of strings", "timestamps", "the closing price column"). Hidden tests usually assert exact shape, so guessing wrong fails every test even when the logic is right.

## Steps
1. Re-read the description and any docstring/example for the exact output contract: keys vs list positions, column names, index labels, element types, string formatting.
2. If the contract is ambiguous, prefer the most literal reading of the stated type and the example output. Do not invent extra nesting or reformat values (e.g. do not join parsed fields back into a string when the example shows tuples).
3. For inputs whose format is not stated, do not assume one canonical format. Accept the common variants: try several parse formats / fall back across plausible column names / handle both str and already-parsed objects. Wrap parsing so an unexpected format raises a clear error rather than crashing on the first item.
4. When a column or key is referenced by a name the task does not guarantee, locate it case-insensitively or by position/type instead of hard-coding one spelling.
5. Before finishing, trace one concrete example from the description through your code and compare the produced value's type and shape to the stated output.

## Pitfalls
- Returning a dict of lists when the example implies a dict of dicts (or vice versa).
- Assuming ISO timestamps or a specific date format when the task never says so.
- Hard-coding a column name that the tests may spell differently.
- Reformatting parsed data (joining fields, changing separators) so it no longer matches the expected element type.
