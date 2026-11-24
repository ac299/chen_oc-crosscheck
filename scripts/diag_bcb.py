"""Which hidden BigCodeBench tests fail, and why (diagnosis only; grades are unchanged).

Reruns every recorded BigCodeBench run's exported workspace against the task's
hidden tests in the grading environment, plus the reference solution as a
control, and writes results/evidence/bcb_failures.json:
  {task: {"gold": {test: "pass"|first error line},
          "runs": {test: {"<method>": [verdict per repeat]}}}}

Run in the grading container (same mounts as scripts/run_one.sh grading phase):
  /venv/bin/python scripts/diag_bcb.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = os.environ.get("XC_TEST_PYTHON", "/env/venv/bin/python")


def first_line(case: ET.Element) -> str:
    for tag in ("failure", "error"):
        el = case.find(tag)
        if el is not None:
            msg = (el.get("message") or el.text or "").strip().splitlines()
            return (msg[0] if msg else tag)[:160]
    return "skipped" if case.find("skipped") is not None else "pass"


def run_tests(tree: Path, task_dir: Path, meta: dict) -> dict[str, str]:
    for tf in meta["test_files"]:
        dst = tree / tf
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(task_dir / "hidden" / tf, dst)
    report = tree.parent / "r.xml"
    env = dict(os.environ, PYTHONPATH=str(tree), PYTHONDONTWRITEBYTECODE="1")
    try:
        subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=", "--timeout", "120",
                        f"--junitxml={report}", *meta["tests"]], cwd=tree, env=env,
                       capture_output=True, text=True, timeout=200)
    except subprocess.TimeoutExpired:
        return {"<all>": "timeout"}
    if not report.exists():
        return {"<all>": "no report (collection error)"}
    return {c.get("name"): first_line(c) for c in ET.parse(report).getroot().iter("testcase")}


def gold_tree(task_dir: Path, meta: dict, dst: Path) -> None:
    shutil.copytree(task_dir / "repo", dst)
    path = dst / meta["completion_file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    idx = lines.index(" " * int(meta["sample"]["indent"]) + "raise NotImplementedError")
    lines[idx:idx + 1] = meta["gold_body"].split("\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [json.loads(l) for l in (ROOT / "results" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("suite") == "bigcodebench" and r["rep"] < 89]
    out: dict[str, dict] = {}
    for task in sorted({r["task"] for r in rows}):
        task_dir = ROOT / "tasks_bcb" / task
        meta = json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            gold_tree(task_dir, meta, Path(tmp) / "repo")
            gold = run_tests(Path(tmp) / "repo", task_dir, meta)
        runs: dict[str, dict[str, list]] = {}
        for r in sorted((r for r in rows if r["task"] == task), key=lambda r: (r["method"], r["rep"])):
            ws = ROOT / "results" / "raw" / r["run_id"] / "workspace"
            if not ws.is_dir():
                res = {"<all>": "no workspace (wall clock)"}
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    shutil.copytree(ws, Path(tmp) / "repo", symlinks=True)
                    res = run_tests(Path(tmp) / "repo", task_dir, meta)
            for name, verdict in res.items():
                runs.setdefault(name, {}).setdefault(r["method"], []).append(verdict)
        out[task] = {"gold": gold, "runs": runs}
        print(task, "gold:", sum(v == "pass" for v in gold.values()), "/", len(gold), flush=True)
    dst = ROOT / "results" / "evidence" / "bcb_failures.json"
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", dst.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
