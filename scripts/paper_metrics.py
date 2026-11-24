"""Two metrics from the OpenCollab paper (Section 3.5, Appendix B.1.3), on the three test sets.

Reads results/runs.jsonl only; no model calls.

1. ITT: Pass@1 of a method minus Pass@1 of Single2 (single-sh), over the same
   (task, repeat) cells.
2. Re-run flip rate: for each method, the share of tasks whose resolved outcome differs
   between two repeats, averaged over the three pairs of repeats (0-1, 0-2, 1-2).

  python scripts/paper_metrics.py
"""

from __future__ import annotations

import json
import os
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SINGLE = "single-sh"
METHODS = ("crosscheck:v7@s2", "duo@s2", "team-collab@s2")


def load() -> dict:
    runs = {}
    for line in (ROOT / "results" / "runs.jsonl").open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue  # a line cut by concurrent appends; scripts/reconcile_runs.py restores the record
        if int(r.get("rep", 9)) < 3:
            runs[(r["task"], r["rep"], r["method"])] = r
    return runs


def test_sets() -> list[tuple[str, set]]:
    plan = [line.split() for line in (ROOT / "plans" / "team_shared_test.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    sets = [("BigCodeBench-Hard", {t for t, _, _ in plan if t.startswith("b_")}),
            ("IO2CodeBench test", set(os.listdir(ROOT / "tasks_io_test"))),
            ("ClassEval", set(os.listdir(ROOT / "tasks_ce")))]
    return sets + [("all three test sets", set().union(*(s for _, s in sets)))]


def resolved(r: dict) -> int:
    return int(bool(r["grade"]["resolved"]))


def main() -> None:
    runs = load()
    sets = test_sets()

    print("== 1. ITT = Pass@1(method) - Pass@1(Single2), same (task, repeat) cells")
    for name, tasks in sets:
        print(f"-- {name}")
        for method in METHODS:
            keys = sorted((t, k) for (t, k, m) in runs if m == method and t in tasks and (t, k, SINGLE) in runs)
            p_m = sum(resolved(runs[(*k, method)]) for k in keys) / len(keys)
            p_s = sum(resolved(runs[(*k, SINGLE)]) for k in keys) / len(keys)
            print(f"   {method:18s} n={len(keys):3d}  Pass@1 {100 * p_m:.1f}%  Single2 {100 * p_s:.1f}%  "
                  f"ITT {100 * (p_m - p_s):+.1f} pp")

    print("\n== 2. Re-run flip rate (share of tasks whose outcome differs between two repeats)")
    for method in (SINGLE,) + METHODS:
        parts = []
        for name, tasks in sets:
            rates = []
            for i, j in combinations(range(3), 2):
                ts = [t for t in tasks if (t, i, method) in runs and (t, j, method) in runs]
                rates.append(sum(resolved(runs[(t, i, method)]) != resolved(runs[(t, j, method)]) for t in ts) / len(ts))
            parts.append(f"{name} {100 * sum(rates) / 3:.1f}%")
        print(f"   {method:18s} " + " | ".join(parts))


if __name__ == "__main__":
    main()
