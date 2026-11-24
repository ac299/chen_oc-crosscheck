"""Gold / stub check for one EvoCodeBench sample (runs inside a container).

python -I check_sample.py <sample_json> <project_dir_ro> <python_of_env>
Copies the project to a temp dir, runs the sample's tests with the original body
(gold) and with the body replaced by `raise NotImplementedError` (stub).
Prints one JSON object: {"gold": ..., "stub": ...} with per-test outcomes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def stub_body(path: Path, body: list[int], indent: int) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    start, end = body[0] - 1, body[1]
    lines[start:end] = [" " * indent + "raise NotImplementedError"]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_tests(root: Path, tests: list[str], python: str, timeout: int = 120) -> dict:
    env = dict(os.environ)
    paths = [str(root)] + ([str(root / "src")] if (root / "src").is_dir() else [])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    report = root.parent / "report.json"
    cmd = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--timeout", str(timeout),
           "-o", "addopts=", f"--junitxml={report}.xml", *tests]
    try:
        proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=timeout + 30)
        out = proc.stdout + proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired:
        return {"code": "timeout", "passed": 0, "failed": 0, "tail": "timeout"}
    import re

    passed = sum(int(x) for x in re.findall(r"(\d+) passed", out))
    failed = sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", out))
    return {"code": code, "passed": passed, "failed": failed, "tail": out.strip().splitlines()[-1][:300] if out.strip() else ""}


def main() -> None:
    sample = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    project, python = Path(sys.argv[2]), sys.argv[3]
    rel = Path(*Path(sample["completion_path"]).parts[1:])
    tests = sample["tests"] if isinstance(sample["tests"], list) else json.loads(sample["tests"].replace("'", '"'))
    body = sample["body_position"]
    body = body if isinstance(body, list) else json.loads(body)
    result = {}
    for mode in ("gold", "stub"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            shutil.copytree(project, root, symlinks=True)
            if mode == "stub":
                stub_body(root / rel, body, int(sample["indent"]))
            # tests without -x so the stub check sees all of them
            res = run_tests(root, tests, python)
            result[mode] = res
    print(json.dumps(result))


if __name__ == "__main__":
    main()
