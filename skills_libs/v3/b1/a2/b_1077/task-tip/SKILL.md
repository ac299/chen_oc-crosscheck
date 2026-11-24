---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The failure is parsing: inputs use day-first format like '01/04/21 12:00:00.000' (DD/MM/YY HH:MM:SS.mmm), which datetime.fromisoformat rejects. Parse with datetime.strptime(ts, '%d/%m/%Y %H:%M:%S.%f') (handle variants: 2-digit year '%y', and possibly missing milliseconds). Treat naive parsed datetimes as UTC (or the source timezone) before astimezone(timezone). Keep the <2 timestamps -> 0.0 early return, use abs total_seconds between consecutive pairs, and return float(np.mean(diffs)). Also handle already-datetime inputs and tz-aware strings gracefully. Verify with day-first strings across timezones and out-of-order lists.
