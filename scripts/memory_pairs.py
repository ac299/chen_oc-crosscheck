"""Paired tables of the two memory experiments (IMPROVEMENTS.md, sections 1.4 and 1.5).

Reads results/runs.jsonl only; no model calls. Each memory arm is paired with its baseline
by (task, repeat), reps 0-2:
  experiment 1: single-sh+mem-{insights,examples,both}        vs single-sh
  experiment 2: crosscheck:v7@s2+tmem-{insights,examples,both} vs crosscheck:v7@s2
Columns: resolved, wins:losses (exact sign test), hidden-test pass rate (Wilcoxon),
Test Designer case validity on the reference (runs where both sides kept a suite),
mean cases, mean / median tokens, mean seconds, resolved per repeat.

  python scripts/memory_pairs.py            # both experiments
  python scripts/memory_pairs.py --exp 2
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from guard_pairs import sign_p, wilcoxon_p  # noqa: E402

EXPERIMENTS = {
    "1": ("single-sh", [f"single-sh+mem-{x}" for x in ("insights", "examples", "both")]),
    "2": ("crosscheck:v7@s2", [f"crosscheck:v7@s2+tmem-{x}" for x in ("insights", "examples", "both")]),
}


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


def validity(r: dict) -> float | None:
    s = r.get("suite_truth") or {}
    return s["valid_on_gold"] / s["cases"] if s.get("cases") else None


def row(name: str, runs: list[dict]) -> str:
    tok = [r.get("tokens") or 0 for r in runs]
    suites = [r["suite_truth"] for r in runs if (r.get("suite_truth") or {}).get("cases")]
    cases = f"{statistics.mean(s['cases'] for s in suites):.1f}" if suites else "-"
    per_rep = " / ".join(str(sum(r["grade"]["resolved"] for r in runs if r["rep"] == k)) for k in range(3))
    return (f"{name:31s} n={len(runs):2d}  resolved {sum(r['grade']['resolved'] for r in runs):2d}  "
            f"hidden {100 * statistics.mean(map(hidden, runs)):.1f}%  cases {cases}  "
            f"tokens {statistics.mean(tok):,.0f} / {statistics.median(tok):,.0f}  "
            f"{statistics.mean(r['seconds'] for r in runs):.0f} s  per repeat {per_rep}")


def compare(runs: dict, base: str, arm: str) -> str:
    keys = sorted((t, k) for (t, k, m) in runs if m == arm and (t, k, base) in runs)
    a = [runs[(*k, arm)] for k in keys]
    b = [runs[(*k, base)] for k in keys]
    wins = sum(x["grade"]["resolved"] and not y["grade"]["resolved"] for x, y in zip(a, b))
    losses = sum(y["grade"]["resolved"] and not x["grade"]["resolved"] for x, y in zip(a, b))
    d = [hidden(x) - hidden(y) for x, y in zip(a, b)]
    out = [row(arm, a),
           f"{'':31s} vs {base}: {wins}:{losses} (sign p = {sign_p(wins, losses):.3f}); "
           f"hidden +{sum(x > 0 for x in d)}/-{sum(x < 0 for x in d)} (Wilcoxon p = {wilcoxon_p(d):.3f})"]
    pv = [(validity(x), validity(y)) for x, y in zip(a, b) if validity(x) is not None and validity(y) is not None]
    if pv:
        dv = [p - q for p, q in pv]
        out.append(f"{'':31s} case validity on {len(pv)} paired runs: "
                   f"{100 * statistics.mean(q for _, q in pv):.1f}% -> {100 * statistics.mean(p for p, _ in pv):.1f}%, "
                   f"+{sum(x > 0 for x in dv)}/-{sum(x < 0 for x in dv)} (Wilcoxon p = {wilcoxon_p(dv):.3f})")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=("1", "2", "all"), default="all")
    exps = ap.parse_args().exp
    runs = load()
    for exp in ("1", "2") if exps == "all" else (exps,):
        base, arms = EXPERIMENTS[exp]
        keys = sorted({(t, k) for (t, k, m) in runs if m == arms[0]})
        print(f"== experiment {exp}: {len(keys)} (task, repeat) pairs")
        print(row(base, [runs[(*k, base)] for k in keys if (*k, base) in runs]))
        for arm in arms:
            print(compare(runs, base, arm))
        print()


if __name__ == "__main__":
    main()
