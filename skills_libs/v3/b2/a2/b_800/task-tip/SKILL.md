---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The crash is `total_goals += goals` where `goals` is a dict (e.g. {'Team A': 2, ...}), not an int. The task says "update it with the given goals and penalties" — the inputs are mappings of team->value, and you must merge them into the CSV's per-team rows, not add them as scalars.

Instead: read existing rows into a dict keyed by team (int-cast goals/penalties). For each team in the `goals` dict, add its value to that team's goals (create the row if absent); same for `penalties`. Write the updated per-team rows back to the CSV (keep the header). Return `Counter` of the *totals* across all rows: `Counter({'goals': sum, 'penalties': sum})`. Handle missing file gracefully. Don't collapse the CSV to a single 'Total' row — preserve team rows.
