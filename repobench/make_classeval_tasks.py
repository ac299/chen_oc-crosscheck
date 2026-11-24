"""Seeded selection of 20 ClassEval tasks (docs/heldout-test-protocol.md).

Runs inside a container with the xc-env-bcb volume at /env (and oc-pythons at
/pythons), the ClassEval checkout read-only at /classeval and the project at
/kaohe/oc-crosscheck:
  /venv/bin/python repobench/make_classeval_tasks.py
Writes tasks_ce/c_<n>/ in the repository-task layout graded by repobench/repograde.py,
and datasets/classeval/screen.jsonl.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SEED = 20261122
TARGET = 20
ROOT = Path("/kaohe/oc-crosscheck")
DATA = Path("/classeval/data/ClassEval_data.json")
OUT = ROOT / "tasks_ce"
SCREEN = ROOT / "datasets" / "classeval" / "screen.jsonl"
PY = "/env/venv/bin/python"
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_]\w*)", re.M)


def modules(*sources: str) -> list[str]:
    return sorted({m for s in sources for m in IMPORT_RE.findall(s)})


def import_error(mods: list[str]) -> str | None:
    if not mods:
        return None
    r = subprocess.run([PY, "-c", "; ".join(f"import {m}" for m in mods)],
                       capture_output=True, text=True, timeout=120)
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
                                "tests/test_solution.py"], cwd=d, env=env, capture_output=True, text=True,
                               timeout=300)
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "tail": "timeout"}
    return {"passed": sum(int(x) for x in re.findall(r"(\d+) passed", out)),
            "failed": sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", out)),
            "tail": out.strip().splitlines()[-1][:200] if out.strip() else ""}


def main() -> None:
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {r["task_id"]: r for r in rows}
    order = sorted(by_id)
    random.Random(SEED).shuffle(order)
    OUT.mkdir(exist_ok=True)
    picked = []
    with SCREEN.open("w", encoding="utf-8") as screen:
        for tid in order:
            r = by_id[tid]
            skeleton, gold = r["skeleton"], r["solution_code"]
            test_src = "from solution import *\n" + r["test"]
            mods = modules(skeleton, gold, r["test"])
            rec = {"task_id": tid, "modules": mods}
            err = import_error(mods)
            if err:
                rec.update(eligible=False, reason="import: " + err)
            else:
                g, s = run_tests(gold, test_src), run_tests(skeleton, test_src)
                ok = g["failed"] == 0 and g["passed"] > 0 and s["failed"] > 0
                rec.update(gold=g, skeleton=s, eligible=ok,
                           reason="ok" if ok else ("gold fails" if not (g["failed"] == 0 and g["passed"])
                                                   else "skeleton passes"))
            screen.write(json.dumps(rec) + "\n")
            screen.flush()
            print(tid, rec["reason"], flush=True)
            if not rec["eligible"]:
                continue
            name = "c_" + tid.replace("ClassEval_", "")
            d = OUT / name
            if d.exists():
                shutil.rmtree(d)
            (d / "repo").mkdir(parents=True)
            (d / "hidden" / "tests").mkdir(parents=True)
            (d / "repo" / "solution.py").write_text(skeleton, encoding="utf-8")
            (d / "hidden" / "tests" / "test_solution.py").write_text(test_src, encoding="utf-8")
            (d / "task.md").write_text(
                f"Implement the class `{r['class_name']}` in `solution.py`. The file holds the class skeleton: "
                "the class description, the constructor and every method with its signature and contract "
                "(docstring, parameters, return value and examples). Implement every method so that it "
                "follows its contract. Keep the class name, the method names and their signatures, and the "
                "imports. Tests are not provided.\n\n```python\n" + skeleton.rstrip() + "\n```\n",
                encoding="utf-8")
            (d / "meta.json").write_text(json.dumps({
                "task_id": name, "source": tid, "class_name": r["class_name"], "modules": mods,
                "completion_file": "solution.py", "tests": ["tests/test_solution.py"],
                "test_files": ["tests/test_solution.py"], "env_volume": "xc-env-bcb",
                "gold_source": gold,
            }, indent=1), encoding="utf-8")
            picked.append(name)
            if len(picked) == TARGET:
                break
    print("SELECTED", picked)


if __name__ == "__main__":
    main()
