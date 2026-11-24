---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The failure is a sign/column mismatch in the transformed values, not validation or plotting. Fit PCA on the data exactly as given (the full DataFrame, no column subsetting/reordering) and return a DataFrame preserving the original index with columns like ['PC1','PC2']. Do not manually flip signs or reorient components. Keep the positive-integer validation (reject bools, non-ints, <=0) and return (DataFrame, Axes). Verify by comparing against a direct PCA(n_components).fit_transform(data) on a DataFrame. Ensure the scatter uses the first two components.
