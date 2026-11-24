"""Agent phase of one experiment run, executed inside an isolated container.

The container sees only: the OpenCollab checkout (read-only, configs/ masked),
this project's code (read-only), ONE task's task.md and repo/ (read-only) and
an output directory. Hidden tests, reference solutions and other runs are not
mounted, so no agent can reach them even with an unrestricted shell.

The provider configuration arrives on stdin, is written to a private file,
loaded once by the OpenCollab client and deleted before any agent starts.

python scripts/run_agent.py --task-dir /task --method duo --run-id X --out /out
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

CFG = Path("/run/oc-config/oc.env")


def load_config_from_stdin() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        return
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_bytes(data)
    os.chmod(CFG, 0o600)
    os.environ["OPENCOLLAB_CONFIG_FILE"] = str(CFG)


def make_workspace(task_dir: Path, ws: Path) -> None:
    shutil.copytree(task_dir / "repo", ws, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    (ws / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "task start"]):
        subprocess.run(cmd, cwd=ws, check=True)


async def run(method: str, ws: Path, goal: str, budget: int, artifacts: Path) -> object:
    from opencollab import OpenCollab

    oc = OpenCollab(str(ws))
    _ = oc.configuration  # resolve configuration now
    if CFG.exists():
        CFG.unlink()  # the key now lives only in this process's memory
    os.environ.pop("OPENCOLLAB_CONFIG_FILE", None)
    # "<method>@s2": every workflow role runs on the Single2 agent profile
    # (docs/duo.md: agent_profile selects the base implementation's prompt,
    # shaping, tool limits and safety; the paper's Duo coders use "the single
    # agent's configuration"). Without the suffix roles use the generic prompt.
    # For team-collab, @s2 selects scripts/teamcfg/team.collab.s2.yaml, which only adds
    # `profile: single2` to every role (paper App. B.1).
    profile = None
    if method.endswith("@s2"):
        method, profile = method[: -len("@s2")], "single2"
    if method == "single":
        # Kept unchanged for the recorded runs. Single2's bash requires an OS
        # process sandbox, which this container does not advertise, so in these
        # runs every bash call was refused ("bash is disabled ..."): the agent
        # could read and edit files but never execute code.
        return await oc.agent(goal, budget=budget, artifacts=str(artifacts))
    if method == "single-sh":
        # Single2 with local shell execution, the same condition as the other
        # methods (allow_unisolated_shell=True). docs/single2.md: "For deliberate
        # local shell execution, pass explicit tools built with
        # builtin_tools(..., headless=False, limits=profile_tool_limits("base"))".
        # Same six tools in the same order and the same Single2 profile/prompt.
        from opencollab.tools import builtin_tools, profile_tool_limits

        tools = builtin_tools("bash", "file_read", "file_write", "apply_patch", "git_diff", "grep",
                              headless=False, limits=profile_tool_limits("base"))
        # "+mem-<layers>" (scripts/run_one_mem.sh): two-layer experience memory on
        # vendor/OpenCollab-skills2 (docs/two-layer-memory-protocol.md).
        mem = {}
        if os.environ.get("XC_MEMORY"):
            layers = os.environ.get("XC_MEMORY_LAYERS", "both")
            mem = {"memory": os.environ["XC_MEMORY"],
                   "memory_layers": ("insights", "examples") if layers == "both" else (layers,)}
        return await oc.agent(goal, tools=tools, budget=budget, artifacts=str(artifacts), **mem)
    if method == "team":
        # Built-in Self-Collaboration team (what `opencollab` starts by default):
        # Analyst (agent 0) delegates to Coder and Tester in isolated worktrees and
        # adopts their changes. Agents decide the handoffs themselves.
        return await oc.team(goal, budget=budget, artifacts=str(artifacts), allow_unisolated_shell=True)
    if method == "team-collab":
        # The repository's prebuilt three-seat team file (configs/team.collab.yaml).
        cfg = "/kaohe/oc-crosscheck/scripts/teamcfg/team.collab.s2.yaml" if profile else "/teamcfg/team.collab.yaml"
        # "<method>+shared" (scripts/run_one.sh) runs on vendor/OpenCollab-fix-budget
        # with seat_budget="shared"; every other run passes nothing, i.e. the
        # framework's original equal split, and works on the unmodified framework.
        extra = {"seat_budget": os.environ["XC_SEAT_BUDGET"]} if os.environ.get("XC_SEAT_BUDGET") else {}
        return await oc.team(goal, config=cfg,
                             prebuild_team=True, budget=budget, artifacts=str(artifacts),
                             allow_unisolated_shell=True, **extra)
    if method == "duo":
        return await oc.workflow("duo", {"goal": goal, "allow_unisolated_shell": True},
                                 budget=budget, artifacts=str(artifacts), agent_profile=profile)
    if method.startswith("crosscheck"):
        variant = method.split(":", 1)[1] if ":" in method else "full"
        wf_args = {"goal": goal, "allow_unisolated_shell": True, "variant": variant}
        # "+mem-<layers>" (scripts/run_one_mem.sh): the Test Designer alone gets the
        # two-layer experience memory (docs/two-layer-memory-protocol.md, v7 section).
        if os.environ.get("XC_MEMORY"):
            layers = os.environ.get("XC_MEMORY_LAYERS", "both")
            wf_args.update(td_memory=os.environ["XC_MEMORY"],
                           td_memory_layers=["insights", "examples"] if layers == "both" else [layers])
        return await oc.workflow("crosscheck", wf_args,
                                 budget=budget, artifacts=str(artifacts), agent_profile=profile)
    raise ValueError(method)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", type=Path, required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget", type=int, default=800_000)
    args = ap.parse_args()
    load_config_from_stdin()

    out = args.out / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    ws = Path("/tmp/ws") / "repo"
    ws.parent.mkdir(parents=True, exist_ok=True)
    make_workspace(args.task_dir, ws)
    goal = (args.task_dir / "task.md").read_text(encoding="utf-8")
    record: dict = {"run_id": args.run_id, "method": args.method,
                    "guard": os.environ.get("OPENCOLLAB_CANDIDATE_PATH_GUARD", "unset"),
                    "framework": os.environ.get("XC_FRAMEWORK", "unknown"),
                    "skills_lib": os.environ.get("XC_SKILLS_LIB"),
                    "seat_budget": os.environ.get("XC_SEAT_BUDGET") or "equal",
                    "memory_layers": os.environ.get("XC_MEMORY_LAYERS")}
    t0 = time.time()
    try:
        base_method = args.method.split("+", 1)[0]
        res = asyncio.run(run(base_method, ws, goal, args.budget, out / "artifacts"))
        record.update(status=res.status, reason=res.reason, tokens=res.tokens,
                      output=res.output if isinstance(res.output, (dict, str)) else str(res.output))
    except Exception as exc:  # noqa: BLE001
        record.update(status="error", reason=repr(exc), tokens=None, trace=traceback.format_exc()[-3000:])
    record["seconds"] = round(time.time() - t0, 1)
    # export the final workspace (source files only) for grading outside this container
    final = out / "workspace"
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(ws, final, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    diff = subprocess.run(["git", "diff", "HEAD"], cwd=ws, capture_output=True, text=True).stdout
    untracked = subprocess.run(["git", "status", "--porcelain"], cwd=ws, capture_output=True, text=True).stdout
    (out / "final.diff").write_text(diff + "\n# status\n" + untracked, encoding="utf-8")
    (out / "record.json").write_text(json.dumps(record, default=str, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: record.get(k) for k in ("run_id", "status", "reason", "tokens", "seconds")}))


if __name__ == "__main__":
    main()
