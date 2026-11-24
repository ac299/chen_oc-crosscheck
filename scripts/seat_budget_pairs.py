"""Tables of the Team seat-budget experiment (IMPROVEMENTS.md, sections 2.4 and 2.5).

Reads results/runs.jsonl only; no model calls. `team-collab@s2+shared` (seat_budget="shared")
is paired with `team-collab@s2` (the original "equal" split) by (task, repeat), reps 0-2, on
the three test sets. A run counts as a budget stop when its end reason contains
"budget exhausted".

  python scripts/seat_budget_pairs.py
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from guard_pairs import sign_p, wilcoxon_p  # noqa: E402

SHARED, EQUAL, V7 = "team-collab@s2+shared", "team-collab@s2", "crosscheck:v7@s2"


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


def hidden(r: dict) -> float:
    g = r["grade"]
    return g["passed"] / g["total"] if g["total"] else 0.0


def stopped(r: dict) -> bool:
    return "budget exhausted" in str(r.get("reason"))


def suites() -> list[tuple[str, set]]:
    plan = [line.split() for line in (ROOT / "plans" / "team_shared_test.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    bcb = {t for t, _, _ in plan if t.startswith("b_")}
    io = set(os.listdir(ROOT / "tasks_io_test"))
    ce = set(os.listdir(ROOT / "tasks_ce"))
    return [("BigCodeBench-Hard", bcb), ("IO2CodeBench test", io), ("ClassEval", ce), ("all", bcb | io | ce)]


def line(name: str, runs: list[dict]) -> str:
    tok = [r.get("tokens") or 0 for r in runs]
    per_rep = " / ".join(str(sum(r["grade"]["resolved"] for r in runs if r["rep"] == k)) for k in range(3))
    return (f"  {name:24s} resolved {sum(r['grade']['resolved'] for r in runs):3d}/{len(runs)}  "
            f"hidden {100 * statistics.mean(map(hidden, runs)):.1f}%  budget stops {sum(map(stopped, runs)):2d}  "
            f"tokens {statistics.mean(tok):,.0f} / {statistics.median(tok):,.0f}  per repeat {per_rep}")


def pairs(a: list[dict], b: list[dict], label: str) -> str:
    wins = sum(x["grade"]["resolved"] and not y["grade"]["resolved"] for x, y in zip(a, b))
    losses = sum(y["grade"]["resolved"] and not x["grade"]["resolved"] for x, y in zip(a, b))
    d = [hidden(x) - hidden(y) for x, y in zip(a, b)]
    return (f"  {label}: resolved {wins}:{losses} (sign p = {sign_p(wins, losses):.3f}); "
            f"hidden +{sum(x > 0 for x in d)}/-{sum(x < 0 for x in d)} (Wilcoxon p = {wilcoxon_p(d):.3f})")


def main() -> None:
    runs = load()
    for name, tasks in suites():
        keys = sorted((t, k) for (t, k, m) in runs if m == SHARED and t in tasks and (t, k, EQUAL) in runs)
        a = [runs[(*k, SHARED)] for k in keys]
        b = [runs[(*k, EQUAL)] for k in keys]
        print(f"== {name}: {len(keys)} pairs")
        print(line("equal (original)", b))
        print(line("shared", a))
        print(pairs(a, b, "shared vs equal"))
        hit = [i for i, y in enumerate(b) if stopped(y)]
        print(f"  pairs where equal stopped on budget: {len(hit)}; resolved there: "
              f"shared {sum(a[i]['grade']['resolved'] for i in hit)}, equal {sum(b[i]['grade']['resolved'] for i in hit)}")
        v = [k for k in keys if (*k, V7) in runs]
        if v:
            c = [runs[(*k, V7)] for k in v]
            s = [runs[(*k, SHARED)] for k in v]
            print(f"  v7 on the same pairs: resolved {sum(r['grade']['resolved'] for r in c)}, "
                  f"hidden {100 * statistics.mean(map(hidden, c)):.1f}%, "
                  f"mean tokens {statistics.mean(r.get('tokens') or 0 for r in c):,.0f}")
            print(pairs(c, s, "v7 vs shared"))
        print()


if __name__ == "__main__":
    main()
