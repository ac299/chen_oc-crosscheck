---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
Your arg handling is still wrong. The signature is task_func(script_path, wait=True, *args), so extra args arrive as a tuple. Do NOT str() them and do NOT flatten a single list/tuple—that mangles values like lists. Pass them through unchanged: cmd = [sys.executable, script_path] + list(args). The failing test likely passes args that must reach the script verbatim (e.g. numbers, flags, or a list) and the script validates sys.argv; your conversion caused a nonzero exit. Keep: ValueError if script missing, return None when wait is False, raise subprocess.CalledProcessError on nonzero return. Verify with a script that echoes/asserts its argv and one that exits nonzero.
