"""Grade a repository task: restore hidden test files into the agent's final
workspace and run the sample's tests with the project environment.

Called by scripts/finish_run.py inside a container started with --network none
and the project's environment volume mounted at /env.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

PYTHON = os.environ.get("XC_TEST_PYTHON", "/env/venv/bin/python")
TIMEOUT = 120


def run(tree: Path, tests: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(tree)] + ([str(tree / "src")] if (tree / "src").is_dir() else []))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
           "--timeout", str(TIMEOUT), *tests]
    try:
        proc = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, timeout=TIMEOUT + 60)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "total": 0, "resolved": False, "tail": "timeout"}
    passed = sum(int(x) for x in re.findall(r"(\d+) passed", out))
    failed = sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", out))
    total = passed + failed
    return {"passed": passed, "failed": failed, "total": total, "resolved": total > 0 and failed == 0,
            "tail": out.strip().splitlines()[-1][:300] if out.strip() else ""}


def grade_repo(task_dir: Path, workspace: Path) -> dict:
    meta = json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "repo"
        shutil.copytree(workspace, tree, symlinks=True)
        for tf in meta["test_files"]:
            dst = tree / tf
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(task_dir / "hidden" / tf, dst)
        return run(tree, meta["tests"])


def suite_truth_repo(task_dir: Path, files: dict[str, str]) -> dict:
    """Run CrossCheck's independent tests on the gold tree and on the stubbed base."""
    meta = json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ("base", "gold"):
            tree = Path(tmp) / mode
            shutil.copytree(task_dir / "repo", tree, symlinks=True)
            if mode == "gold" and "gold_source" in meta:
                # ClassEval: the reference is a whole file, not one function body
                (tree / meta["completion_file"]).write_text(meta["gold_source"], encoding="utf-8")
            elif mode == "gold":
                path = tree / meta["completion_file"]
                lines = path.read_text(encoding="utf-8").split("\n")
                body = meta["sample"]["body_position"]
                body = body if isinstance(body, list) else json.loads(body)
                stub = " " * int(meta["sample"]["indent"]) + "raise NotImplementedError"
                idx = lines.index(stub, body[0] - 1)
                lines[idx:idx + 1] = meta["gold_body"].split("\n")
                path.write_text("\n".join(lines), encoding="utf-8")
            for rel, text in files.items():
                f = tree / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text, encoding="utf-8")
            report = Path(tmp) / f"{mode}.xml"
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join([str(tree)] + ([str(tree / "src")] if (tree / "src").is_dir() else []))
            subprocess.run([PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
                            f"--junitxml={report}", *sorted(files)],
                           cwd=tree, env=env, capture_output=True, text=True, timeout=TIMEOUT + 60)
            import xml.etree.ElementTree as ET

            if report.exists():
                for case in ET.parse(report).getroot().iter("testcase"):
                    k = f"{case.get('classname', '')}::{case.get('name')}"
                    bad = case.find("failure") is not None or case.find("error") is not None or case.find("skipped") is not None
                    out.setdefault(k, {})[mode] = "fail" if bad else "pass"
    return {k: {"gold": v.get("gold", "error"), "base": v.get("base", "error")} for k, v in out.items()}
