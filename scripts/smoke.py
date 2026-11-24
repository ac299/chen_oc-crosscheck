"""Smoke test: one tiny single-agent run against the configured model.

Creates a throwaway git repo under /work/smoke (Docker volume), asks the
agent to add a function, then prints status, tokens and metric keys.
Never prints configuration secrets.
"""

import asyncio
import json
import shutil
import subprocess
import time
from pathlib import Path

from opencollab import OpenCollab

WS = Path("/work/smoke")


def make_repo() -> None:
    if WS.exists():
        shutil.rmtree(WS)
    WS.mkdir(parents=True)
    (WS / "mathx.py").write_text("def add(a, b):\n    return a + b\n")
    subprocess.run(["git", "init", "-q"], cwd=WS, check=True)
    subprocess.run(["git", "add", "-A"], cwd=WS, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=WS, check=True)


async def main() -> None:
    make_repo()
    oc = OpenCollab(str(WS))
    t0 = time.time()
    res = await oc.agent(
        "In mathx.py add a function mul(a, b) returning a*b. Do not run tests.",
        budget=40_000,
        max_steps=8,
    )
    dt = time.time() - t0
    print("status:", res.status, "reason:", res.reason)
    print("tokens:", res.tokens, "seconds:", round(dt, 1))
    print("metrics keys:", sorted(res.metrics))
    print("metrics:", json.dumps(res.metrics, default=str)[:1500])
    print("file:\n" + (WS / "mathx.py").read_text())


asyncio.run(main())
