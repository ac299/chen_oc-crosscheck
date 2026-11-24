"""Validate every tasks_repo task with the grading code itself.

The stubbed repo must fail the hidden tests and the repo with the gold body
restored must pass them. Run inside a container with the task's env volume:
  python repobench/validate_tasks.py <task_id>
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path("/kaohe/oc-crosscheck")
sys.path.insert(0, str(ROOT / "repobench"))
from repograde import grade_repo  # noqa: E402


def main() -> None:
    task = ROOT / "tasks_repo" / sys.argv[1]
    meta = json.loads((task / "meta.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        gold = Path(tmp) / "repo"
        shutil.copytree(task / "repo", gold, symlinks=True)
        path = gold / meta["completion_file"]
        lines = path.read_text(encoding="utf-8").split("\n")
        body = meta["sample"]["body_position"]
        body = body if isinstance(body, list) else json.loads(body)
        stub_line = " " * int(meta["sample"]["indent"]) + "raise NotImplementedError"
        idx = lines.index(stub_line, body[0] - 1)
        lines[idx:idx + 1] = meta["gold_body"].split("\n")
        path.write_text("\n".join(lines), encoding="utf-8")
        gold_res = grade_repo(task, gold)
    # gold first: a hanging stub test can leave a server holding a port (deluder)
    stub = grade_repo(task, task / "repo")
    ok = gold_res["resolved"] and not stub["resolved"]
    print(json.dumps({"task": sys.argv[1], "ok": ok, "stub": f"{stub['passed']}/{stub['total']}",
                      "gold": f"{gold_res['passed']}/{gold_res['total']}", "gold_tail": gold_res.get("tail", "")[:160]}))


if __name__ == "__main__":
    main()
