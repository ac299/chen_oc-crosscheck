"""Mechanism probe: run only the v3 Spec Analyst and the spec gate on one task.

Used to check that the gate works on real analyst output before any v3
evaluation run. Not an evaluation: no code is written and nothing is graded.
Run through scripts/probe_spec.sh (same isolation as run_one.sh).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/kaohe/oc-crosscheck")
CFG = Path("/run/oc-config/oc.env")


async def main() -> None:
    data = sys.stdin.buffer.read()
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_bytes(data)
    os.chmod(CFG, 0o600)
    os.environ["OPENCOLLAB_CONFIG_FILE"] = str(CFG)
    from opencollab import OpenCollab
    from opencollab.tools import builtin_tools

    from workflows import crosscheck as cc
    from xc import prompts as P
    from xc import specgate

    ws = Path("/tmp/ws/repo")
    shutil.copytree("/task/repo", ws)
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "start"]):
        subprocess.run(cmd, cwd=ws, check=True)
    goal = Path("/task/task.md").read_text(encoding="utf-8")
    oc = OpenCollab(str(ws))
    _ = oc.configuration
    CFG.unlink()
    os.environ.pop("OPENCOLLAB_CONFIG_FILE", None)

    async def flow(ctx, _args):
        spec = await ctx.agent(P.SPEC_PROMPT_V3.format(goal=goal), schema=cc.SPEC_SCHEMA_V3, label="spec",
                               tools=list(builtin_tools("file_read", "grep")), budget=cc.BUDGET["spec"])
        res = specgate.gate(spec, goal)
        return {"summary": res.summary(), "contract": specgate.render(res), "spec": spec,
                "verified": [r["behavior"] for r in res.verified],
                "ruled_out": [(r["behavior"], r["gate"]) for r in res.ruled_out]}

    out = await oc.workflow(flow, {}, budget=200_000)
    print(json.dumps({"status": out.status, "tokens": out.tokens, **(out.output or {})}, ensure_ascii=False, default=str))


asyncio.run(main())
