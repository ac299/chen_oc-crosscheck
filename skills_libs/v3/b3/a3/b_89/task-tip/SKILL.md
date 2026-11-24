---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The crash: `data` is a NumPy array, not a DataFrame, so `data.index` fails. Handle both: if it's a DataFrame use `.index`/`.loc`; otherwise use `np.arange(len(data))` and boolean-mask indexing. Compute Z-scores on the raw column values (e.g. `stats.zscore(data[column])` or StandardScaler on the column), take absolute values, compare to threshold. Return `(original_data, filtered_data, outlier_indices)` where indices are the positions/indices of removed rows; return the original data object unchanged, not a copy. Keep two scatter plots titled exactly 'Data with Outliers' and 'Data without Outliers'; make plotting robust (don't assume a DataFrame index). Verify with both a plain ndarray and a DataFrame input.
