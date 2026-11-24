"""Hidden-test grader.

grade_dir(task_dir, solution_dir) copies the solution's source files into a
fresh temp directory together with the task's hidden tests, runs pytest and
returns (passed, failed, total). Agents never see hidden/ or reference/.

CLI: python scripts/grade.py --check     validates every task:
     hidden tests must fail on the initial repo and pass on the reference.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASKS = Path(__file__).resolve().parent.parent / "tasks"


def _copy_sources(src: Path, dst: Path) -> None:
    for path in src.rglob("*.py"):
        rel = path.relative_to(src)
        if rel.parts[0] in {"tests", "hidden", ".git"} or "__pycache__" in rel.parts:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def grade_dir(task_dir: Path, solution_dir: Path, timeout: float = 120) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        _copy_sources(task_dir / "repo", work)  # baseline files
        _copy_sources(solution_dir, work)  # candidate overrides
        shutil.copytree(task_dir / "hidden", work / "hidden_tests")
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "hidden_tests"]
        try:
            proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=timeout)
            out = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "total": 0, "resolved": False, "error": "timeout"}
    passed = sum(int(x) for x in re.findall(r"(\d+) passed", out))
    failed = sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", out))
    total = passed + failed
    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "resolved": total > 0 and failed == 0,
        "tail": out.strip().splitlines()[-1] if out.strip() else "",
    }


def check_all() -> bool:
    ok = True
    for task in sorted(p for p in TASKS.iterdir() if (p / "task.md").exists()):
        start = grade_dir(task, task / "repo")
        ref = grade_dir(task, task / "reference")
        good = ref["resolved"] and not start["resolved"]
        ok &= good
        print(f"{task.name:14s} initial {start['passed']:3d}/{start['total']:3d}  "
              f"reference {ref['passed']:3d}/{ref['total']:3d}  {'OK' if good else 'BAD'}")
        if not ref["resolved"]:
            print("   reference:", ref.get("tail"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        sys.exit(0 if check_all() else 1)
