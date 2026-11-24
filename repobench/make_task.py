"""Turn selected EvoCodeBench samples into agent tasks (see docs/repobench-protocol.md).

python -I repobench/make_task.py
For each entry of datasets/evocodebench/selected.json creates tasks_repo/<id>/:
  task.md     the prompt every method receives
  repo/       the project with the target body replaced by `raise NotImplementedError`
              and the test files holding the sample's tests removed
  hidden/     those removed test files (same relative paths), used only for grading
  meta.json   sample record, project, env volume, completion file, test ids
"""

from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DS = ROOT / "datasets" / "evocodebench"
OUT = ROOT / "tasks_repo"


def as_list(value):
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return ast.literal_eval(value)


def as_dict(value):
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return ast.literal_eval(value)


def task_id(project: str, namespace: str) -> str:
    return "r_" + re.sub(r"[^a-z0-9]+", "_", f"{project}_{namespace.split('.')[-1]}".lower()).strip("_")


def prompt(sample: dict, rel: str, sig: list[int], signature: str) -> str:
    req = as_dict(sample["requirement"])
    lines = [
        f"In this repository, the {sample['type']} `{sample['namespace']}` in `{rel}` has lost its "
        f"implementation: its body is `raise NotImplementedError`. Implement it.",
        "",
        f"Signature (line {sig[0]} of `{rel}`):",
        "```python",
        signature.rstrip(),
        "```",
        "",
        "Requirement:",
    ]
    for key, value in req.items():
        lines.append(f"- {key}: {str(value).strip()}")
    lines += [
        "",
        "Keep the signature and the rest of the repository unchanged except where the implementation",
        "needs it. Tests for this function are not provided; the repository's other code and tests show",
        "how it is used. Run Python and tests with `python` from the repository root.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    selected = json.loads((DS / "selected.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for entry in selected:
        s, project = entry["sample"], entry["project"]
        tid = task_id(project, s["namespace"])
        dst = OUT / tid
        if dst.exists():
            print("exists", tid)
            continue
        src = DS / "src" / "Source_Code" / project
        rel = str(Path(*Path(s["completion_path"]).parts[1:])).replace("\\", "/")
        tests = as_list(s["tests"])
        test_files = sorted({t.split("::")[0] for t in tests})
        repo = dst / "repo"
        shutil.copytree(src, repo, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "._*"))
        sig, body = as_list(s["signature_position"]), as_list(s["body_position"])
        path = repo / rel
        lines = path.read_text(encoding="utf-8").split("\n")
        signature = "\n".join(lines[sig[0] - 1:sig[1]])
        gold_body = "\n".join(lines[body[0] - 1:body[1]])
        lines[body[0] - 1:body[1]] = [" " * int(s["indent"]) + "raise NotImplementedError"]
        path.write_text("\n".join(lines), encoding="utf-8")
        for tf in test_files:
            target = dst / "hidden" / tf
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(repo / tf), str(target))
        (dst / "task.md").write_text(prompt(s, rel, sig, signature), encoding="utf-8")
        (dst / "meta.json").write_text(json.dumps({
            "task_id": tid, "project": project, "namespace": s["namespace"], "completion_file": rel,
            "tests": tests, "test_files": test_files,
            "env_volume": "xc-env-" + project.lower().replace("_", "-"),
            "gold_body": gold_body, "sample": s,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        print("created", tid, rel, len(tests), "tests in", test_files)


if __name__ == "__main__":
    main()
