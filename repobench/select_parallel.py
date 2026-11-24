"""Parallel version of repobench/screen_select.py with an identical selection result.

Projects are screened concurrently (each project's own samples stay in their
seeded order and stop at the first eligible one), then the final choice walks the
projects in the seeded order exactly as select.py does. Because a project's
outcome does not depend on any other project, the selected set is the same as
the sequential walk; only wall time changes. Reuses screen.jsonl (resumable).

python -I repobench/select_parallel.py [workers]
"""

from __future__ import annotations

import json
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import importlib.util  # noqa: E402

# Load repobench/screen_select.py under another name: importing it as `select` would
# shadow the stdlib module that subprocess depends on.
_spec = importlib.util.spec_from_file_location("rb_select", Path(__file__).resolve().parent / "screen_select.py")
seq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seq)

LOCK = threading.Lock()


def log(rec: dict) -> None:
    with LOCK:
        seq.log(rec)


def screen_project(project: str, samples: list[dict], seen: dict) -> dict | None:
    env = seen["env"].get(project)
    if env is None:
        env = {"kind": "env", "project": project, "ok": seq.build_env(project)}
        log(env)
    if not env["ok"]:
        return None
    samples = sorted(samples, key=lambda r: r["namespace"])
    random.Random(f"{seq.SEED}:{project}").shuffle(samples)
    for s in samples:
        key = f"{project}:{s['namespace']}"
        rec = seen["sample"].get(key)
        if rec is None:
            res = seq.check(s, project)
            gold_ok = res.get("gold", {}).get("failed", 1) == 0 and res.get("gold", {}).get("passed", 0) > 0
            stub_bad = res.get("stub", {}).get("failed", 0) > 0
            rec = {"kind": "sample", "project": project, "namespace_key": key, "result": res,
                   "eligible": bool(gold_ok and stub_bad),
                   "reason": "ok" if gold_ok and stub_bad else ("gold fails" if not gold_ok else "stub passes")}
            log(rec)
        if rec["eligible"]:
            return {"project": project, "namespace": s["namespace"], "sample": s}
    return None


def main() -> None:
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rows = [json.loads(l) for l in (seq.DS / "meta" / "data.jsonl").read_text(encoding="utf-8").splitlines()]
    by_project: dict[str, list[dict]] = {}
    for r in rows:
        by_project.setdefault(r["completion_path"].split("/")[0], []).append(r)
    order = sorted(by_project)
    random.Random(seq.SEED).shuffle(order)
    seen = seq.done()
    results: dict[str, dict | None] = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {p: pool.submit(screen_project, p, by_project[p], seen) for p in order}
        for p in order:
            results[p] = futures[p].result()
            picked = [x for x in (results[q] for q in order if q in results) if x]
            # stop scheduling more once the first 10 in seeded order are settled
            settled = all(q in results for q in order[: order.index(p) + 1])
            if settled and len(picked) >= seq.TARGET:
                for f in futures.values():
                    f.cancel()
                break
    selected = [results[p] for p in order if results.get(p)][: seq.TARGET]
    (seq.DS / "selected.json").write_text(json.dumps(selected, indent=1, ensure_ascii=False), encoding="utf-8")
    print("SELECTED", len(selected), [f"{x['project']}:{x['namespace']}" for x in selected], flush=True)


if __name__ == "__main__":
    main()
