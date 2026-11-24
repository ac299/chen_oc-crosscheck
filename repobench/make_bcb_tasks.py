"""Seeded selection of 3 BigCodeBench-Hard tasks (docs/bigcodebench-protocol.md).

Runs inside a container with the xc-env-bcb volume at /env and network access:
  /venv/bin/python repobench/make_bcb_tasks.py
Writes tasks_bcb/<id>/ in the same layout as tasks_repo/ so the repository grader
(repobench/repograde.py) can grade it, and datasets/bigcodebench/screen.jsonl.
"""

from __future__ import annotations

import importlib
import json
import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

SEED = 20261121
TARGET = int(__import__("os").environ.get("XC_BCB_TARGET", "3"))
ROOT = Path("/kaohe/oc-crosscheck")
DS = ROOT / "datasets" / "bigcodebench"
OUT = ROOT / "tasks_bcb"
PY = "/env/venv/bin/python"
STUB = "    raise NotImplementedError"


def libs_import(libs: list[str]) -> str | None:
    code = "; ".join(f"import {l}" for l in libs)
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, timeout=120)
    return None if r.returncode == 0 else (r.stderr.strip().splitlines() or ["import failed"])[-1][:200]


def run_tests(solution_src: str, test_src: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "solution.py").write_text(solution_src, encoding="utf-8")
        (d / "tests").mkdir()
        (d / "tests" / "test_solution.py").write_text(test_src, encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=str(d), MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
        try:
            r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--timeout", "120",
                                "tests/test_solution.py"], cwd=d, env=env, capture_output=True, text=True, timeout=200)
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "tail": "timeout"}
    import re

    return {"passed": sum(int(x) for x in re.findall(r"(\d+) passed", out)),
            "failed": sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", out)),
            "tail": out.strip().splitlines()[-1][:200] if out.strip() else ""}


def main() -> None:
    rows = json.loads((DS / "hard_v0.1.4.json").read_text(encoding="utf-8"))
    by_id = {r["task_id"]: r for r in rows}
    order = sorted(by_id)
    random.Random(SEED).shuffle(order)
    OUT.mkdir(exist_ok=True)
    screen = (DS / "screen.jsonl").open("w", encoding="utf-8")
    picked = []
    for tid in order:
        r = by_id[tid]
        libs = eval(r["libs"])  # noqa: S307 - literal list from the dataset
        rec = {"task_id": tid, "libs": libs}
        err = libs_import(libs)
        test_src = "from solution import *\n" + r["test"]
        stub_src = r["code_prompt"].rstrip("\n") + "\n" + STUB + "\n"
        gold_src = r["code_prompt"].rstrip("\n") + "\n" + r["canonical_solution"].rstrip("\n") + "\n"
        if err:
            rec.update(eligible=False, reason="import: " + err)
        else:
            gold, stub = run_tests(gold_src, test_src), run_tests(stub_src, test_src)
            ok = gold["failed"] == 0 and gold["passed"] > 0 and stub["failed"] > 0
            rec.update(gold=gold, stub=stub, eligible=ok,
                       reason="ok" if ok else ("gold fails" if not (gold["failed"] == 0 and gold["passed"]) else "stub passes"))
        screen.write(json.dumps(rec) + "\n"); screen.flush()
        print(tid, rec["reason"], flush=True)
        if not rec["eligible"]:
            continue
        name = "b_" + tid.replace("BigCodeBench/", "")
        d = OUT / name
        if d.exists():
            shutil.rmtree(d)
        (d / "repo").mkdir(parents=True)
        (d / "hidden" / "tests").mkdir(parents=True)
        (d / "repo" / "solution.py").write_text(stub_src, encoding="utf-8")
        (d / "hidden" / "tests" / "test_solution.py").write_text(test_src, encoding="utf-8")
        stub_line = stub_src.split("\n").index(STUB) + 1
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
    screen.close()
    print("SELECTED", picked)


if __name__ == "__main__":
    main()
