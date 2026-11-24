---
name: spec-to-implementation
description: "Use when implementing one function from a natural-language description with a fixed signature and no tests."
---
## When to use
A task gives a prose description plus a fixed signature/imports and asks you to fill in one function body. No tests are provided.

## Steps
1. Read the spec twice and extract a contract: parameter meanings, return type/shape, documented exceptions, and every 'Note'/'If ... then ...' edge case. Write these as a short checklist.
2. Preserve the given imports and signature exactly; only replace the placeholder body. Do not add new top-level imports unless the spec's imports are insufficient (prefer what is provided).
3. Implement the happy path first, then add each documented edge case (empty input, single element, missing files, invalid values) as explicit branches.
4. Match the exact return type: if the spec says a DataFrame with named columns/index, a tuple of specific types, or a list of strings, construct precisely that, not a lookalike.
5. Raise the exact exception types named in the spec at the exact conditions stated; use the documented message semantics.
6. If the spec includes a worked example or doctest-like output, reproduce it mentally and check your logic yields it.

## Pitfalls
- Returning a wrong container type (e.g. dict vs DataFrame) or wrong column/index labels.
- Forgetting documented zero/empty-input behavior (often return a default like 0.0 or an empty structure rather than raising).
- Adding validation the spec did not ask for, or omitting one it did.
- Changing the signature or imports, which breaks the harness.
