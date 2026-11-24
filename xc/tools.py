"""Custom tool: load a previous candidate patch into a fresh candidate worktree.

OpenCollab candidates always start from the source tree. A repair round needs
to start from a candidate's patch instead, so the repair agent first calls
this tool, which runs `git apply` inside its own isolated environment.
"""

from __future__ import annotations

from typing import Any


class LoadStartingPoint:
    name = "load_starting_point"
    description = (
        "Apply the implementation you are asked to repair to your working tree. "
        "Call this exactly once, before reading or editing any file."
    )
    parameters = {"type": "object", "properties": {}, "additionalProperties": False}
    default_timeout = 60.0
    disable_outer_timeout = False

    def __init__(self, patch: str) -> None:
        self._patch = patch
        self.applied = False

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": self.parameters},
        }

    async def execute_with_runtime(self, params: dict[str, Any], runtime: Any) -> str:
        if self.applied:
            return "The starting point is already applied."
        env = getattr(runtime, "environment", None)
        if env is None:
            return "Error: no execution environment available."
        result = await env.exec_cmd(
            "git apply --whitespace=nowarn -", timeout=60.0, input_bytes=self._patch.encode("utf-8"),
        )
        code = getattr(result, "exit_code", getattr(result, "returncode", None))
        text = str(getattr(result, "output", "") or getattr(result, "stdout", "") or "")
        if code not in (0, None):
            return f"Error applying starting point (exit {code}): {text[-500:]}"
        self.applied = True
        return "Starting point applied. Inspect the files and repair them."
