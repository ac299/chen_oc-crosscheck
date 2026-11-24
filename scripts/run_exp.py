"""Run one (task, method, repeat) and record outcome, tokens and time.

python scripts/run_exp.py --task t4_allocate --method single --rep 0
Methods: single (OpenCollab Single2), duo (built-in Duo), crosscheck (ours).
Each run gets a fresh git workspace under /work/runs. The agent sees only
task.md and repo/. Hidden tests are applied afterwards by scripts/grade.py.
Results are appended as JSON lines to results/runs.jsonl.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

from opencollab import OpenCollab

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from grade import grade_dir  # noqa: E402

TASKS = ROOT / "tasks"
RUNS = Path("/work/runs")
RESULTS = ROOT / "results" / "runs.jsonl"


def make_workspace(task: str, run_id: str) -> Path:
    ws = RUNS / run_id
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(TASKS / task / "repo", ws)
    (ws / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "task start"]):
        subprocess.run(cmd, cwd=ws, check=True)
    return ws


def goal_text(task: str) -> str:
    return (TASKS / task / "task.md").read_text(encoding="utf-8")


async def run_method(method: str, ws: Path, goal: str, budget: int, artifacts: Path) -> object:
    oc = OpenCollab(str(ws))
    if method == "single":
        return await oc.agent(goal, budget=budget, artifacts=str(artifacts))
    if method == "duo":
        return await oc.workflow(
            "duo", {"goal": goal, "allow_unisolated_shell": True},
            budget=budget, artifacts=str(artifacts),
        )
    if method.startswith("crosscheck"):
        variant = method.split(":", 1)[1] if ":" in method else "full"
        return await oc.workflow(
            "crosscheck", {"goal": goal, "allow_unisolated_shell": True, "variant": variant},
            budget=budget, artifacts=str(artifacts),
        )
    raise ValueError(method)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--budget", type=int, default=600_000)
    args = ap.parse_args()

    run_id = f"{args.task}__{args.method.replace(':', '-')}__r{args.rep}__{int(time.time())}"
    ws = make_workspace(args.task, run_id)
    artifacts = RUNS / (run_id + "__artifacts")
    t0 = time.time()
    record: dict = {"run_id": run_id, "task": args.task, "method": args.method, "rep": args.rep}
    try:
        res = asyncio.run(run_method(args.method, ws, goal_text(args.task), args.budget, artifacts))
        record.update(
            status=res.status, reason=res.reason, tokens=res.tokens,
            output=res.output if isinstance(res.output, (dict, str)) else str(res.output),
        )
    except Exception as exc:  # noqa: BLE001 - record and keep the batch going
        record.update(status="error", reason=repr(exc), tokens=None, trace=traceback.format_exc()[-2000:])
    record["seconds"] = round(time.time() - t0, 1)
    record["grade"] = grade_dir(TASKS / args.task, ws)
    record["artifacts"] = str(artifacts)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
    out = {k: record[k] for k in ("run_id", "status", "reason", "tokens", "seconds")}
    out["grade"] = {k: record["grade"].get(k) for k in ("passed", "total", "resolved")}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
