---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
Your merge logic was right, but the totals were wrong: you summed the whole file after merging, so pre-existing rows were counted again. The expected Counter reflects only the *incremental* totals — the sum of the goals/penalties values you were given (e.g. empty/zero inputs -> Counter({'goals':0,'penalties':0}); a second call with the same dicts should not double-count prior file contents). So compute totals from the input mappings themselves (sum of goals.values(), sum of penalties.values()), while still merging into the CSV per-team rows and preserving the header. Also handle negative values (penalties can go negative) and missing files without crashing. Keep returning a Counter with keys 'goals' and 'penalties'.
