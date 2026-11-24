---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The failures are all `TypeError: Argument 'freq' has incorrect type (expected str, got int)` from `pd.date_range(freq=step)`. Hidden tests pass `step` as an integer, not a pandas offset string. Handle both: if `step` is an int, convert it to a valid frequency string (e.g. `f'{step}min'` or `f'{step}s'`) before calling `date_range`; if it's already a string, pass it through. Also verify the trend is added correctly and that the returned object is the Axes with labels 'Time' and 'Value'. Keep `np.random.seed(seed)` for reproducibility. Test with integer steps to confirm no TypeError.
