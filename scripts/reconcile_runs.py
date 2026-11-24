"""Restore graded records that are missing from results/runs.jsonl.

finish_run.py writes each record twice: into results/raw/<run_id>/graded_record.json
and as one appended line of runs.jsonl. Run this only while no batch is running.
Records already in runs.jsonl or in results/evidence/excluded_runs.jsonl are left alone.

  python scripts/reconcile_runs.py           # report only
  python scripts/reconcile_runs.py --apply   # append the missing records
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ids(path: Path) -> set[str]:
    out = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                out.add(json.loads(line)["run_id"])
            except (ValueError, KeyError):
                pass
    return out


def main() -> None:
    runs = ROOT / "results" / "runs.jsonl"
    known = ids(runs) | ids(ROOT / "results" / "evidence" / "excluded_runs.jsonl")
    missing = []
    for f in sorted((ROOT / "results" / "raw").glob("*/graded_record.json")):
        line = f.read_text(encoding="utf-8")
        if json.loads(line)["run_id"] not in known:
            missing.append(line if line.endswith("\n") else line + "\n")
    print(f"missing from runs.jsonl: {len(missing)}")
    for line in missing:
        print("  ", json.loads(line)["run_id"])
    if missing and "--apply" in sys.argv:
        with runs.open("a", encoding="utf-8") as fh:
            fh.writelines(missing)
        print("appended")


if __name__ == "__main__":
    main()
