---
name: self-verify-no-tests
description: "Use when no tests are provided and you must confirm a function meets its documented behavior and edge cases."
---
## When to use
You implemented (or are about to finish) a function and the task says tests are not provided, so you must validate it yourself.

## Steps
1. Write a throwaway script outside the repo (or a temp file) that imports the function and calls it with representative inputs.
2. Cover the documented edge cases explicitly: empty input, single element, boundary values, and each documented exception path (wrap in try/except and assert the right exception type).
3. For file/process/network functions, create temporary fixtures (temp dirs, small files, local ports) and clean them up; assert on returned paths/types and side effects.
4. For plotting/DataFrame returns, assert the returned object type and key attributes (columns, index, axes type) rather than visual output.
5. Run the script, fix failures, rerun until all checks pass. Remove the throwaway script before finishing.

## Pitfalls
- Only testing the happy path and missing the documented empty/invalid branches.
- Leaving temp files, servers, or scripts in the working tree.
- Asserting on exact floating values without tolerance.
- Assuming a library is installed; if an import fails, note it rather than silently skipping the check.
