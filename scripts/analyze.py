"""Aggregate results/runs.jsonl into tables for the README.

Cost: every llm_call event in a run's trace carries provider usage with cache
hits. Prices are deepseek-flash peak rates as reported by third-party pricing
pages in Nov 2026 (input miss $0.30/M, cache hit $0.006/M, output $1.20/M);
they are not verified against DeepSeek's own page and only scale the totals.

python scripts/analyze.py [--methods single,team,duo,crosscheck] [--md out.md]
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE: str | None = "dev"
TASKS: set[str] | None = None  # --tasks-from: only these tasks (e.g. the 33 BigCodeBench test tasks)
PRICE = {"miss": 0.30, "hit": 0.006, "out": 1.20}  # USD per million tokens


def usage(run_id: str) -> dict:
    tot = {"calls": 0, "input": 0, "cached": 0, "output": 0}
    art = ROOT / "results" / "raw" / run_id / "artifacts"
    seen = set()
    for f in art.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "llm_call":
                continue
            p = e.get("payload") or {}
            key = (p.get("response_session_id"), p.get("session_step"), e.get("timestamp"))
            if key in seen:
                continue
            seen.add(key)
            u = p.get("usage") or {}
            tot["calls"] += 1
            tot["input"] += int(u.get("input_tokens") or 0)
            tot["cached"] += int(u.get("cache_read_tokens") or 0)
            tot["output"] += int(u.get("output_tokens") or 0)
    miss = tot["input"] - tot["cached"]
    tot["cost"] = (miss * PRICE["miss"] + tot["cached"] * PRICE["hit"] + tot["output"] * PRICE["out"]) / 1e6
    return tot


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def sign_test(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def load(methods: list[str] | None) -> list[dict]:
    rows = []
    for line in (ROOT / "results" / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue  # a line cut by concurrent appends; its record is restored by scripts/reconcile_runs.py
        if methods and r["method"] not in methods:
            continue
        if TASKS is not None and r["task"] not in TASKS:
            continue
        if r.get("rep", 0) >= 89:  # smoke/regression runs (89 and up)
            continue
        if SUITE and r.get("suite", "dev") != SUITE:
            continue
        r["usage"] = usage(r["run_id"])
        rows.append(r)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--suite", default="dev", help="dev | io2code | evocodebench | bigcodebench | io2code_test | classeval | all")
    ap.add_argument("--tasks-from", default="", help="plan file; only its tasks are analysed")
    args = ap.parse_args()
    global SUITE
    SUITE = None if args.suite == "all" else args.suite
    global TASKS
    if args.tasks_from:
        TASKS = {l.split()[0] for l in Path(args.tasks_from).read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")}
    methods = [m for m in args.methods.split(",") if m] or None
    rows = load(methods)
    order = methods or sorted({r["method"] for r in rows}, key=lambda m: ["single", "team", "duo"].index(m)
                                    if m in ("single", "team", "duo") else 9)
    out = []

    # ---- overall table
    out.append("| method | runs | resolved | 95% CI | mean hidden pass | mean tokens | median tokens | mean cost $ | mean s | failed status | escape runs |")
    out.append("|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|")
    by_m = defaultdict(list)
    for r in rows:
        by_m[r["method"]].append(r)
    for m in order:
        rs = by_m[m]
        if not rs:
            continue
        k = sum(r["grade"]["resolved"] for r in rs)
        lo, hi = wilson(k, len(rs))
        frac = sum(r["grade"]["passed"] / max(1, r["grade"]["total"]) for r in rs) / len(rs)
        toks = sorted(r["usage"]["input"] + r["usage"]["output"] for r in rs)
        med = toks[len(toks) // 2]
        avg = sum(toks) / len(toks)
        cost = sum(r["usage"]["cost"] for r in rs) / len(rs)
        secs = sum(r["seconds"] for r in rs) / len(rs)
        bad = sum(r.get("status") != "completed" for r in rs)
        esc = sum(r["audit"]["escape_calls"] > 0 for r in rs)
        out.append(f"| {m} | {len(rs)} | {k} ({k / len(rs):.0%}) | {lo:.0%}–{hi:.0%} | {frac:.1%} | "
                   f"{avg:,.0f} | {med:,} | {cost:.4f} | {secs:.0f} | {bad} | {esc} |")

    # ---- per task
    tasks = sorted({r["task"] for r in rows})
    out.append("")
    out.append("Resolved runs per task (out of repeats), mean tokens in thousands")
    out.append("")
    out.append("| task | " + " | ".join(order) + " |")
    out.append("|---|" + "---|" * len(order))
    for t in tasks:
        cells = []
        for m in order:
            rs = [r for r in by_m[m] if r["task"] == t]
            if not rs:
                cells.append("-")
                continue
            k = sum(r["grade"]["resolved"] for r in rs)
            tk = sum(r["usage"]["input"] + r["usage"]["output"] for r in rs) / len(rs) / 1000
            cells.append(f"{k}/{len(rs)} · {tk:.0f}k")
        out.append(f"| {t} | " + " | ".join(cells) + " |")

    # ---- paired comparisons vs crosscheck (by task and repeat)
    target = next((m for m in order if m.startswith("crosscheck")), None)
    if target:
        out.append("")
        out.append(f"Paired by (task, repeat) against {target}: wins = only {target} resolved")
        out.append("")
        out.append("| baseline | pairs | both | only " + target + " | only baseline | neither | sign-test p |")
        out.append("|---|---:|---:|---:|---:|---:|---:|")
        idx = {(r["task"], r["rep"], r["method"]): r for r in rows}
        for m in order:
            if m == target:
                continue
            both = only_t = only_b = neither = 0
            for (t, rep, mm), r in idx.items():
                if mm != target or (t, rep, m) not in idx:
                    continue
                a, b = r["grade"]["resolved"], idx[(t, rep, m)]["grade"]["resolved"]
                both += a and b
                only_t += a and not b
                only_b += b and not a
                neither += not a and not b
            n = both + only_t + only_b + neither
            out.append(f"| {m} | {n} | {both} | {only_t} | {only_b} | {neither} | {sign_test(only_t, only_b):.3f} |")

    # ---- crosscheck internals
    cc = [r for r in rows if r["method"].startswith("crosscheck")]
    if cc:
        out.append("")
        out.append("CrossCheck: where runs stopped")
        out.append("")
        out.append("| level | runs | resolved | mean tokens (k) |")
        out.append("|---|---:|---:|---:|")
        lv = defaultdict(list)
        for r in cc:
            rep = (r.get("output") or {}).get("report", {}) if isinstance(r.get("output"), dict) else {}
            lv[rep.get("level")].append(r)
        names = {1: "L1 verify", 2: "L2 audit", 3: "L3 repair", 4: "L4 diversify", None: "error"}
        for level in sorted(lv, key=lambda x: (x is None, x)):
            rs = lv[level]
            k = sum(r["grade"]["resolved"] for r in rs)
            tk = sum(r["usage"]["input"] + r["usage"]["output"] for r in rs) / len(rs) / 1000
            out.append(f"| {names.get(level, level)} | {len(rs)} | {k} | {tk:.0f} |")
        st = [r["suite_truth"] for r in cc if r.get("suite_truth")]
        if st:
            cases = sum(s["cases"] for s in st)
            valid = sum(s["valid_on_gold"] for s in st)
            b2g = sum(s["base_to_gold"] for s in st)
            out.append("")
            out.append(f"Independent suites: {len(st)} runs, {cases} cases, {valid} valid on reference "
                       f"({valid / cases:.1%}), {b2g} fail-on-base-and-pass-on-reference ({b2g / cases:.1%}).")
        au = [r["auditor"] for r in cc if r.get("auditor")]
        if au:
            j = sum(a["judged"] for a in au)
            c = sum(a["correct"] for a in au)
            out.append(f"Auditor: {j} verdicts, {c} correct ({c / j:.0%}); kept invalid {sum(a['kept_invalid'] for a in au)}, "
                       f"dropped valid {sum(a['dropped_valid'] for a in au)}.")
        # false stops: stopped early but hidden tests failed
        early = [r for r in cc if ((r.get("output") or {}).get("report", {}) or {}).get("level") in (1, 2, 3)]
        fs = [r["run_id"] for r in early if not r["grade"]["resolved"]]
        out.append(f"Early stops (L1–L3): {len(early)}; of these unresolved on hidden tests: {len(fs)} {fs}")

    text = "\n".join(out)
    print(text)
    if args.md:
        Path(args.md).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
