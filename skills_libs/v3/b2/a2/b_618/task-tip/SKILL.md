---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The failures come from `randint(0, goals - 1)` / `randint(0, penalties - 1)` when the argument is 0 (or 1), producing an empty range. The parameters are upper bounds passed to `randint`, so use `randint(0, goals)` and `randint(0, penalties)` directly (inclusive), which also handles 0 gracefully. Keep the DataFrame columns exactly `['Team', 'Goals', 'Penalty Cost']`, with Penalty Cost = penalties drawn * PENALTY_COST. Return the two seaborn Axes in a list (goals first, penalty costs second). Verify with goals=0/penalties=0 and small values, and confirm the returned objects are Axes and the DataFrame has one row per team in TEAMS.
