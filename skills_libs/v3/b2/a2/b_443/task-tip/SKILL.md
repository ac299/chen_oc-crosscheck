---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The tensor product was wrong. Hidden tests expect the flattened result to have one element per (i,j) pair of P's rows and T's leading dims, i.e. length = P.shape[0]*T.shape[1] (e.g. 12, not 36). Don't use tensordot over P's last axis; instead compute the product so each P row contracts with T's first axis, giving shape (P.shape[0], T.shape[1], T.shape[2]) then flatten to (-1,1). Verify length matches P.shape[0]*T.shape[1]. Also the KMeans got only 2 distinct clusters from 3 requested (ConvergenceWarning) because flattened values were duplicated/wrong; fixing the product shape should give enough distinct points. Keep fit_predict, title exactly 'KMeans Clustering Visualization', and return (cluster_result, ax). Test with small arrays to confirm cluster_result length equals flattened length.
