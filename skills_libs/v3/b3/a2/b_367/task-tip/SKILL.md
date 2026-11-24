---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
Your code dropped days with zero activities, so the bar chart had fewer bars than expected and tests indexing bars by weekday position failed (IndexError / wrong heights). Always plot all seven days in fixed Monday→Sunday order, using counts of 0 for missing days. Build counts with a defaultdict over all weekdays, then pass the full 7-element day list and matching counts to ax.bar. Also validate types robustly: reject non-datetime entries (including subclasses? plain isinstance is fine) and handle empty lists without error—still produce 7 zero-height bars. Don't filter days by presence. Keep labels/title exactly as specified. Verify by checking len(ax.patches)==7 and each patch height equals the count for that weekday, including empty input and single-day input.
