"""Extra train split for skill evolution v3: BigCodeBench-Hard eligible tasks 54-73.

Copy of evolve/make_val_tasks.py with TARGET 73: tasks 1-53 are taken from the
recorded screening datasets/bigcodebench/screen_53.jsonl and never rewritten.

Continues the seeded order and eligibility rules of repobench/make_bcb_tasks.py
(docs/bigcodebench-protocol.md). The first 33 eligible tasks already exist in
tasks_bcb/ and are only checked against that order, never rewritten. Runs in a
container with the xc-env-bcb volume at /env:
  /venv/bin/python evolve/make_val_tasks.py
Writes tasks_bcb/<id>/ for the new tasks and datasets/bigcodebench/screen_53.jsonl.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "/kaohe/oc-crosscheck/repobench")
import make_bcb_tasks as m  # noqa: E402

TARGET = 73
EXISTING = 53


def main() -> None:
    rows = json.loads((m.DS / "hard_v0.1.4.json").read_text(encoding="utf-8"))
    by_id = {r["task_id"]: r for r in rows}
    order = sorted(by_id)
    random.Random(m.SEED).shuffle(order)
    # The first 33 are fixed by the recorded screening, not by re-screening:
    # network-dependent tasks (e.g. BigCodeBench/1012) can flip between screenings.
    recorded = [json.loads(line) for line in (m.DS / "screen_53.jsonl").open(encoding="utf-8")]
    verdict = {r["task_id"]: r["eligible"] for r in recorded}
    assert [r["task_id"] for r in recorded] == order[: len(recorded)], "recorded screening is not the seeded order"
    assert sum(verdict.values()) == EXISTING
    picked: list[str] = []
    with (m.DS / "screen_73.jsonl").open("w", encoding="utf-8") as screen:
        for tid in order:
            name = "b_" + tid.replace("BigCodeBench/", "")
            if tid in verdict:
                if verdict[tid]:
                    picked.append(name)
                screen.write(json.dumps({"task_id": tid, "eligible": verdict[tid], "reason": "recorded"}) + "\n")
                continue
            r = by_id[tid]
            libs = eval(r["libs"])  # noqa: S307 - literal list from the dataset
            rec = {"task_id": tid, "libs": libs}
            test_src = "from solution import *\n" + r["test"]
            stub_src = r["code_prompt"].rstrip("\n") + "\n" + m.STUB + "\n"
            gold_src = r["code_prompt"].rstrip("\n") + "\n" + r["canonical_solution"].rstrip("\n") + "\n"
            err = m.libs_import(libs)
            if err:
                rec.update(eligible=False, reason="import: " + err)
            else:
                gold, stub = m.run_tests(gold_src, test_src), m.run_tests(stub_src, test_src)
                ok = gold["failed"] == 0 and gold["passed"] > 0 and stub["failed"] > 0
                rec.update(gold=gold, stub=stub, eligible=ok, reason="ok" if ok else "gold fails or stub passes")
            screen.write(json.dumps(rec) + "\n")
            screen.flush()
            print(tid, rec["reason"], flush=True)
            if not rec["eligible"]:
                continue
            if len(picked) < EXISTING:
                raise SystemExit(f"{name} is eligible but missing from tasks_bcb: the order does not match")
            d = m.OUT / name
            if d.exists():
                raise SystemExit(f"{d} already exists")
            (d / "repo").mkdir(parents=True)
            (d / "hidden" / "tests").mkdir(parents=True)
            (d / "repo" / "solution.py").write_text(stub_src, encoding="utf-8")
            (d / "hidden" / "tests" / "test_solution.py").write_text(test_src, encoding="utf-8")
            stub_line = stub_src.split("\n").index(m.STUB) + 1
            (d / "task.md").write_text(
                r["instruct_prompt"].rstrip() + "\n\nImplement `task_func` in `solution.py` (its body is currently "
                "`raise NotImplementedError`); keep the imports and the signature. Tests are not provided.\n",
                encoding="utf-8")
            (d / "meta.json").write_text(json.dumps({
                "task_id": name, "source": tid, "libs": libs, "completion_file": "solution.py",
                "tests": ["tests/test_solution.py"], "test_files": ["tests/test_solution.py"],
                "env_volume": "xc-env-bcb", "gold_body": r["canonical_solution"].rstrip("\n"),
                "sample": {"body_position": [stub_line, stub_line], "indent": 4},
            }, indent=1), encoding="utf-8")
            picked.append(name)
            if len(picked) == TARGET:
                break
    existing = sorted(p.parent.name for p in m.OUT.glob("*/meta.json"))
    assert sorted(picked[:EXISTING]) == sorted(set(existing) - set(picked[EXISTING:])), "existing set mismatch"
    print("ORDER", json.dumps(picked))
    print("TRAIN2", json.dumps(picked[EXISTING:]))


if __name__ == "__main__":
    main()
