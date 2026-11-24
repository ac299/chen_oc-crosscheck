---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
Your code parsed CSV rows and rejoined them, losing the original tuple/row structure and changing line numbering. The expected Content is the CSV row as parsed (e.g. a tuple like ('name', 'age')), not a rejoined string. Also, line numbers should be sequential positions in the diff output (1-based across the merged diff), not per-file counters: for a change, the '-' line and '+' line get consecutive numbers (2 and 3), then the next unchanged line is 4. So: read each file with csv.reader into lists of tuples (do not join), check emptiness, run ndiff on those row lists, and enumerate the ndiff results starting at 1, using status=line[0] and content=line[2:] (the tuple). Keep FileNotFoundError/ValueError/Exception handling. Verify with a small CSV where one row differs.
