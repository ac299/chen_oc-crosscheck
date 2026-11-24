---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The prior attempt deleted the file inside task_func, but tests inspect it after return; deletion belongs to test teardown. Do not call os.remove or os.rmdir. Create task_func_data with os.makedirs(exist_ok=True), open 'task_func_data/Output.txt' in append mode, and write the header only if the file is new/empty (check os.path.getsize or existence before opening) so repeated calls don't duplicate headers. Append random temperature and humidity rows (with a timestamp column is fine). Return exactly the string 'task_func_data/Output.txt' (os.path.join yields the same on POSIX). Leave the file on disk after returning. Verify by calling twice and confirming one header and growing rows.
