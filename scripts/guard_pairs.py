"""Paired comparison duo vs duo+guard on the development tasks.

Pairs runs by (task, rep). Reports, for the first batch (reps 0-2, the two arms
run hours apart), the interleaved replication (reps 3-7, same session) and all:
resolved (exact two-sided sign test), and tokens / seconds (median of paired
differences, share of pairs where guard is lower, Wilcoxon signed-rank test with
the normal approximation).

  python scripts/guard_pairs.py [--md results/guard_pairs.md]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sign_p(a: int, b: int) -> float:
    n, k = a + b, min(a, b)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def wilcoxon_p(diffs: list[float]) -> float:
    d = [x for x in diffs if x != 0]
    n = len(d)
    if n == 0:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    tie_term = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    w_plus = sum(r for r, x in zip(ranks, d) if x > 0)
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - tie_term / 48
    z = (abs(w_plus - mean) - 0.5) / math.sqrt(var) if var > 0 else 0.0
    return min(1.0, math.erfc(max(z, 0) / math.sqrt(2)))


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def block(name: str, pairs: list[tuple[dict, dict]]) -> list[str]:
    n = len(pairs)
    if not n:
        return [f"| {name} | 0 | | | | | | |"]
    off = sum(a["grade"]["resolved"] for a, _ in pairs)
    on = sum(b["grade"]["resolved"] for _, b in pairs)
    only_on = sum(1 for a, b in pairs if b["grade"]["resolved"] and not a["grade"]["resolved"])
    only_off = sum(1 for a, b in pairs if a["grade"]["resolved"] and not b["grade"]["resolved"])
    rows = []
    for key in ("tokens", "seconds"):
        ok = [(a[key], b[key]) for a, b in pairs if a.get(key) is not None and b.get(key) is not None]
        diffs = [float(b) - float(a) for a, b in ok]
        lower = sum(1 for x in diffs if x < 0)
        rows.append(f"median {median([float(a) for a, _ in ok]):,.0f} → {median([float(b) for _, b in ok]):,.0f}; "
                    f"paired median diff {median(diffs):+,.0f}; guard lower in {lower}/{len(diffs)}; "
                    f"Wilcoxon p={wilcoxon_p(diffs):.3f}")
    return [f"| {name} | {n} | {off}/{n} → {on}/{n} | {only_on} : {only_off} (p={sign_p(only_on, only_off):.3f}) "
            f"| {rows[0]} | {rows[1]} |"]



def _read_runs(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue  # a line cut by concurrent appends; scripts/reconcile_runs.py restores the record
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    args = ap.parse_args()
    runs = _read_runs(ROOT / "results" / "runs.jsonl")
    by = {}
    for r in runs:
        if r.get("suite", "dev") == "dev" and r["method"] in ("duo", "duo+guard") and r["rep"] < 89:
            by[(r["task"], r["rep"], r["method"])] = r
    keys = sorted({(t, rep) for t, rep, _ in by})
    pairs = {k: (by[(*k, "duo")], by[(*k, "duo+guard")]) for k in keys
             if (*k, "duo") in by and (*k, "duo+guard") in by}
    first = [v for (t, rep), v in pairs.items() if rep <= 2]
    second = [v for (t, rep), v in pairs.items() if rep >= 3]
    lines = ["| batch | pairs | resolved off → on | only guard : only off | tokens (off → on) | seconds (off → on) |",
             "|---|---:|---|---|---|---|"]
    lines += block("reps 0-2 (arms run hours apart)", first)
    lines += block("reps 3-7 (interleaved, same session)", second)
    lines += block("all", list(pairs.values()))
    text = "\n".join(lines)
    print(text)
    if args.md:
        Path(args.md).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
