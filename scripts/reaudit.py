"""Recompute the trace audit for every run with the current scripts/audit.py.

Early runs were audited with an earlier rule set (which, for example, counted
Single2's own workspace as an escape). Run this after a batch has finished;
it rewrites results/runs.jsonl in place and keeps a .bak copy.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit import audit_run  # noqa: E402

src = ROOT / "results" / "runs.jsonl"
shutil.copy2(src, src.with_suffix(".jsonl.bak"))
out = []
for line in src.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    r["audit"] = audit_run(ROOT / "results" / "raw" / r["run_id"] / "artifacts")
    out.append(json.dumps(r, default=str, ensure_ascii=False))
src.write_text("\n".join(out) + "\n", encoding="utf-8")
print(len(out), "runs re-audited")
