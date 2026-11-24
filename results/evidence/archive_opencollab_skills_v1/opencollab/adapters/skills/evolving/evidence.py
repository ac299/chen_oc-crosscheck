"""Run outcomes and skill usage read back from trajectories."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class RunOutcome:
    """One graded run. ``(task, rep)`` pairs a run with its counterpart in another arm."""

    task: str
    rep: int
    resolved: bool
    run_id: str = ""
    tokens: int | None = None
    seconds: float | None = None
    skills_used: tuple[str, ...] = ()
    # Free-form evidence for the reflector: task text, diff, failing checks.
    details: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


def skills_used(trajectory: str | os.PathLike[str]) -> tuple[str, ...]:
    """Skills a run loaded, in call order, from ``tool_exec`` records of ``use_skill``."""
    names: list[str] = []
    path = Path(trajectory)
    if not path.is_file():
        return ()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = record.get("payload") or {}
            if record.get("type") != "tool_exec" or payload.get("tool") != "use_skill":
                continue
            name = (payload.get("args") or {}).get("name")
            result = str(payload.get("result") or "")
            if isinstance(name, str) and not result.startswith("Unknown skill"):
                names.append(name)
    return tuple(names)


def resolve_rate(outcomes: Iterable[RunOutcome]) -> float | None:
    items = list(outcomes)
    return sum(o.resolved for o in items) / len(items) if items else None


__all__ = ["RunOutcome", "resolve_rate", "skills_used"]
