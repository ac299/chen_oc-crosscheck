"""Record runs killed by the 40-minute wall clock as unresolved (paper App. B.1:
a run that reaches the wall clock stays in every denominator).

A run killed by `timeout 2400` in batch.sh leaves a summary line with no JSON in
results/batch.log and no record in runs.jsonl. This script appends a record for each
such (task, method, rep) given on the command line, and moves any later record for
the same triple (a second attempt) to results/evidence/excluded_runs.jsonl.

python scripts/record_timeouts.py "<task> <method> <rep> <HH:MM:SS of the kill>" ...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs.jsonl"
EXCL = ROOT / "results" / "evidence" / "excluded_runs.jsonl"


def main() -> None:
    items = [a.split() for a in sys.argv[1:]]
    rows = [json.loads(l) for l in RUNS.read_text(encoding="utf-8").splitlines()]
    keep, moved = [], []
    keys = {(t, m, int(r)) for t, m, r, _ in items}
    for r in rows:
        (moved if (r["task"], r["method"], r["rep"]) in keys else keep).append(r)
    for r in moved:
        r["excluded_reason"] = ("second attempt of a run that hit the 40-minute wall clock; the first attempt "
                                "counts as unresolved (paper App. B.1), so this rerun is not used")
    suite = lambda t: "evocodebench" if (ROOT / "tasks_repo" / t).is_dir() else (
        "io2code" if (ROOT / "tasks_io" / t).is_dir() else "dev")
    for t, m, r, when in items:
        keep.append({"run_id": f"{t}__{m}__r{r}__timeout-{when}", "task": t, "method": m, "rep": int(r),
                     "suite": suite(t), "status": "stopped", "reason": "wall clock: killed after 2400 s",
                     "tokens": None, "seconds": 2400, "output": {}, "grade": {"passed": 0, "failed": 0,
                     "total": 0, "resolved": False, "tail": "wall clock"},
                     "audit": {"roles": {}, "escape_calls": 0, "escape_kinds": {}, "escapes": [], "benign": 0}})
    RUNS.write_text("".join(json.dumps(r, default=str, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")
    with EXCL.open("a", encoding="utf-8") as fh:
        for r in moved:
            fh.write(json.dumps(r, default=str, ensure_ascii=False) + "\n")
    print(f"recorded {len(items)} timeouts, moved {len(moved)} later attempts")


if __name__ == "__main__":
    main()
