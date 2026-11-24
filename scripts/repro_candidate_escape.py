"""Offline reproduction: do workflow candidates stay inside their own worktree?

No model API is used. A scripted model drives the built-in file tools
(file_read / file_write only, no bash, allow_unisolated_shell not set).

Scenario
  * Candidates A and B run in parallel through ctx.candidate_agent.
  * A writes answer.py in its own worktree, then waits.
  * With --bash, B also runs `cat` / `echo >` on the same paths through the
    bash tool (headless=False, i.e. what allow_unisolated_shell=true grants).
  * B uses file_read with the ABSOLUTE path of A's answer.py
    (real agents found such paths with `find /`, see results/evidence).
  * B also tries file_write with an absolute path into the SOURCE workspace.
  * Control: a plain Single2 session (oc.agent) attempts the same absolute
    read of a file outside its workspace.

Usage (inside the experiment container):
  python -I scripts/repro_candidate_escape.py            # current checkout
  OPENCOLLAB_CANDIDATE_PATH_GUARD=0 python -I ...        # guard disabled
  PYTHONPATH=/tmp/oc-main python -I ...                  # upstream main export
Prints one JSON line with what each probe returned.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import opencollab
from opencollab import OpenCollab
from opencollab.adapters.candidate_workspace import EnvCandidateWorkspace
from opencollab.adapters.env import LocalEnvironment
from opencollab.adapters.llm.types import LLMResponse, Usage
from opencollab.tools import builtin_tools


def tool_call(cid: str, name: str, args: dict) -> LLMResponse:
    return LLMResponse(
        tool_calls=[{"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}],
        usage=Usage(4, 2), finish_reason="tool_calls",
    )


def done() -> LLMResponse:
    return LLMResponse(content="done", usage=Usage(4, 2), finish_reason="stop")


def last_tool_result(messages: list) -> str:
    for m in reversed(messages):
        if m.get("role") == "tool":
            return str(m.get("content"))
    return ""


class RecordingCandidates(EnvCandidateWorkspace):
    def __init__(self, environment):
        super().__init__(environment)
        self.leases = []

    async def acquire(self, label):
        lease = await super().acquire(label)
        self.leases.append((label, lease))
        return lease


class Script:
    """One scripted model shared by both candidates; routes by prompt text."""

    def __init__(self, backend, source: Path, with_bash: bool):
        self.backend, self.source, self.with_bash = backend, source, with_bash
        self.a_written = asyncio.Event()
        self.b_done = asyncio.Event()
        self.observed: dict[str, str] = {}

    def _workspace(self, label: str) -> str:
        return next(lease.environment.workspace for lab, lease in self.backend.leases if lab == label)

    async def complete(self, messages, **_kw):
        prompt = next(m["content"] for m in messages if m.get("role") == "user")
        steps = sum(1 for m in messages if m.get("role") == "tool")
        if prompt.startswith("ROLE A"):
            if steps == 0:
                return tool_call("a1", "file_write", {"path": "answer.py", "mode": "create",
                                                       "content": "SECRET_FROM_A = 42\n"})
            self.a_written.set()
            await asyncio.wait_for(self.b_done.wait(), 20)
            return done()
        # ROLE B
        if steps == 0:
            await asyncio.wait_for(self.a_written.wait(), 20)
            target = str(Path(self._workspace("cand-a")) / "answer.py")
            self.observed["sibling_path"] = target
            return tool_call("b1", "file_read", {"path": target})
        if steps == 1:
            self.observed["b_read_sibling"] = last_tool_result(messages)[:200]
            return tool_call("b2", "file_write", {"path": str(self.source / "planted.txt"), "mode": "create",
                                                   "content": "written by candidate B\n"})
        if steps == 2:
            self.observed["b_write_source"] = last_tool_result(messages)[:200]
            if not self.with_bash:
                self.b_done.set()
                return done()
            target = self.observed["sibling_path"]
            return tool_call("b3", "bash", {"command": f"cat {target}"})
        if steps == 3:
            self.observed["b_bash_read_sibling"] = last_tool_result(messages)[:200]
            return tool_call("b4", "bash", {"command": f"echo planted-by-bash > {self.source}/planted_bash.txt"})
        if steps == 4:
            self.observed["b_bash_write_source"] = last_tool_result(messages)[:200]
            self.b_done.set()
            return done()
        return done()


class SingleProbe:
    def __init__(self, target: str):
        self.target, self.observed = target, None

    async def complete(self, messages, **_kw):
        if not any(m.get("role") == "tool" for m in messages):
            return tool_call("s1", "file_read", {"path": self.target})
        self.observed = last_tool_result(messages)[:200]
        return done()


def make_repo(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "base.py").write_text("x = 1\n")
    for args in (("init", "-q"), ("add", "-A"),
                 ("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return root


async def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="repro-"))
    source = make_repo(tmp / "source")
    outside = tmp / "outside_secret.txt"
    outside.write_text("outside the workspace\n")
    environment = LocalEnvironment(str(source))
    backend = RecordingCandidates(environment)
    with_bash = "--bash" in sys.argv
    script = Script(backend, source, with_bash)
    names = ("file_read", "file_write", "bash") if with_bash else ("file_read", "file_write")
    tools = builtin_tools("file_read", "file_write")

    async def flow(ctx, _inputs):
        a, b = await ctx.parallel([
            lambda: ctx.candidate_agent("ROLE A", label="cand-a", tools=builtin_tools(*names, headless=not with_bash)),
            lambda: ctx.candidate_agent("ROLE B", label="cand-b", tools=builtin_tools(*names, headless=not with_bash)),
        ])
        return {"a_diff": a.diff if a else None, "b_diff": b.diff if b else None}

    result = await OpenCollab(source, environment=environment, model="controlled").workflow(
        flow, llm=script, candidate_workspace=backend, trace=False,
        limit_mode="explicit", budget=20000, max_steps=6, timeout=60,
    )
    single = SingleProbe(str(outside))
    await OpenCollab(source, model="controlled").agent(
        "probe", llm=single, tools=tools, budget=10000, max_steps=3, trace=False,
    )
    out = {
        "opencollab_file": opencollab.__file__,
        "workflow_status": result.status,
        "workflow_reason": result.reason,
        "candidate_B_read_sibling_file": script.observed.get("b_read_sibling"),
        "candidate_B_write_into_source": script.observed.get("b_write_source"),
        "planted_file_exists_in_source": (source / "planted.txt").exists(),
        "bash_mode": with_bash,
        "candidate_B_bash_read_sibling": script.observed.get("b_bash_read_sibling"),
        "candidate_B_bash_write_source": script.observed.get("b_bash_write_source"),
        "bash_planted_file_exists_in_source": (source / "planted_bash.txt").exists(),
        "single2_read_outside_file": single.observed,
    }
    print(json.dumps(out, indent=1, default=str))
    await environment.cleanup()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
