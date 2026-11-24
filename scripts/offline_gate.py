"""Offline check for the v7 idea (no model calls).

Question: if Single2 is the fast path, can an independent Test Designer suite tell
when Single2 is wrong? For every Single2 IO2CodeBench run we take its final
program.py and run on it every independent suite that CrossCheck's Test Designer
wrote for the same task in other runs. A suite "flags" the program if any case fails.

Reported per suite-run pair, then per Single2 run (fraction of suites that flag):
  detection   = P(flag | Single2 wrong on hidden tests)
  false alarm = P(flag | Single2 right on hidden tests)
Run inside the experiment container without network:
  python scripts/offline_gate.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from xc import executor as ex  # noqa: E402


def main() -> None:
    rows = [json.loads(l) for l in (ROOT / "results" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    io = [r for r in rows if r.get("suite") == "io2code" and r["rep"] < 90]
    suites = defaultdict(list)
    for r in io:
        if not r["method"].startswith("crosscheck"):
            continue
        f = ROOT / "results" / "raw" / r["run_id"] / "indep_tests.json"
        if f.exists():
            files = json.loads(f.read_text(encoding="utf-8"))
            if files:
                suites[r["task"]].append((r["run_id"], files))
    singles = [r for r in io if r["method"] == "single"]
    pair = {"wrong": [0, 0], "right": [0, 0]}  # [flagged, total]
    per_run = []
    for r in singles:
        prog = ROOT / "results" / "raw" / r["run_id"] / "workspace" / "program.py"
        if not prog.exists() or not suites[r["task"]]:
            continue
        right = r["grade"]["resolved"]
        flags = 0
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base"
            shutil.copytree(ROOT / "tasks_io" / r["task"] / "repo", base)
            shutil.copy2(prog, base / "program.py")
            for _, files in suites[r["task"]]:
                out = ex.run_tests(base, "", files)
                flagged = bool(out.collect_error) or bool(out.failed)
                flags += flagged
                key = "right" if right else "wrong"
                pair[key][0] += flagged
                pair[key][1] += 1
        per_run.append({"run": r["run_id"], "task": r["task"], "single_right": right,
                        "suites": len(suites[r["task"]]), "flag_rate": round(flags / len(suites[r["task"]]), 2)})
    for row in per_run:
        print(f"{row['task'][3:30]:28s} single {'right' if row['single_right'] else 'WRONG'}  "
              f"flagged by {row['flag_rate']:.0%} of {row['suites']} suites")
    for k in ("wrong", "right"):
        f, t = pair[k]
        label = "detection (Single2 wrong)" if k == "wrong" else "false alarm (Single2 right)"
        print(f"{label:30s}: {f}/{t} suite-run pairs = {f / t:.0%}" if t else f"{label}: n/a")
    Path(ROOT / "results" / "offline_gate.json").write_text(json.dumps({"per_run": per_run, "pairs": pair}, indent=1))


if __name__ == "__main__":
    main()
