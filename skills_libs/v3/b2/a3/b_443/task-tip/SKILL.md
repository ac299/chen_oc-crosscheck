---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The prior fix still reduced the wrong axis. Required: product shape (P.shape[0], T.shape[1], T.shape[2]) — contract P's last axis with T's first axis only, no extra .sum(). Use np.tensordot(P, T, axes=([1],[0])) and flatten with .reshape(-1,1); do NOT sum the trailing axis. Verify flattened length == P.shape[0]*T.shape[1]*T.shape[2] (e.g. 12 for the failing case, not 36 or 6). The duplicate-point ConvergenceWarning came from collapsing values; keeping the full tensor product yields distinct points so KMeans returns n_clusters labels. Return fit_predict output (labels array) and ax with exact title 'KMeans Clustering Visualization'. Sanity-check with small random arrays that len(cluster_result)==flattened.shape[0] and unique labels count is reasonable.
