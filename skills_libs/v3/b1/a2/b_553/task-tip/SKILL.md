---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
Your happy path works, but the hidden tests exercise empty inputs, and pandas' plot raises on empty/zero-column DataFrames. Handle these explicitly instead of relying on df.plot:

- If len(a)==0 or len(b)==0, build the figure/axes yourself (e.g. fig, ax = plt.subplots()) and return ax without calling df.plot. This avoids 'no numeric data to plot' and the IndexError from empty bar plotting.
- Only call df.plot(kind='bar') when there is at least one row and one column.
- Keep columns as COLUMNS[:len(b)] and index=a; ensure values are numeric (np.random.rand is fine).
- Guard len(b) > len(COLUMNS) if relevant, but the main fix is the empty-case branch.

Verify by calling task_func([], []), task_func([], ['x']), and task_func(['r'], []) and confirming each returns a matplotlib.axes.Axes.
