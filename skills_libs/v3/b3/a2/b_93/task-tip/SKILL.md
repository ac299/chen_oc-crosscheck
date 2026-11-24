---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The failure is a sign/column mismatch in the transformed values, not the validation or plotting. The agent filtered to numeric columns and passed a raw numpy array to PCA, which can produce different component signs/orientations than expected. Likely the expected behavior is to fit PCA on the full DataFrame (or the data as given) and return a DataFrame with the same index and default/PC column naming, letting sklearn handle it. Do not reorder or subset columns, and do not manually flip signs. Keep the positive-integer validation (reject bools, non-ints, <=0) and return (DataFrame, Axes). Verify by comparing against a direct `PCA(n_components).fit_transform(data)` on a DataFrame, preserving index and using columns like ['PC1','PC2']. Also ensure the scatter uses the first two components.
