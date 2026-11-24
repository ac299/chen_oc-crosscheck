"""Reject edits that encode one task instead of a class of tasks.

arXiv 2609.39148 found that skills which transfer badly to held-out tasks
"fix details that should depend on the task, such as column names and output
files, or turn a fix for one failure into a rule for every task". Two checks
target those two failure modes before an edit costs any gate runs:

1. a rule check for identifiers and literals that occur in only a few training tasks;
2. an LLM judge asked whether the edit is a general procedure or a one-task patch.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable, Mapping

from opencollab.adapters.skills.evolving.reflector import AUTHORING_GUIDE, Edit

Ask = Callable[[str], Awaitable[str]]

_PATTERNS = (
    re.compile(r"`([^`\n]{3,60})`"),                       # inline code
    re.compile(r"'([A-Za-z_][\w .\-/]{2,40})'"),            # quoted literals
    re.compile(r'"([A-Za-z_][\w .\-/]{2,40})"'),
    re.compile(r"\b([A-Za-z]+_[A-Za-z0-9_]+)\b"),            # snake_case identifiers
    re.compile(r"\b([a-z]+[A-Z][A-Za-z0-9]+)\b"),            # camelCase identifiers
    re.compile(r"\b([\w\-]+\.(?:csv|json|txt|xlsx|py|png|db|log|zip|xml|html))\b"),
)

JUDGE_PROMPT = """\
You review one proposed edit to a skill library used by a coding agent on many different tasks.
Decide whether the edit is a GENERAL procedure that helps a class of tasks, or a TASK-SPECIFIC
patch that only encodes details of the tasks it was learned from (their function or column names,
expected values, output files), or that turns one fix into a rule for every task.

{guide}
Edit:
{edit}

Reply with one JSON object and nothing else: {{"verdict": "general" or "task_specific", "reason": "<short>"}}
"""


@dataclass(frozen=True)
class ScreenResult:
    passed: bool
    hits: tuple[str, ...]
    verdict: str
    reason: str


_IDENTIFIER_LIKE = re.compile(r"[_\d./]|[a-z][A-Z]")


def _identifier_like(term: str) -> bool:
    """Only identifiers and literals that cannot be ordinary prose words.

    A plain word such as ``date`` or ``name`` occurs in task text and in any
    general skill alike, so the rule check would reject every skill (seen in
    round 1 of the first evolution run). Plain words are left to the judge.
    """
    return bool(_IDENTIFIER_LIKE.search(term))


def term_index(task_texts: Mapping[str, str]) -> dict[str, set[str]]:
    """Map each identifier-like term to the training tasks that mention it."""
    index: dict[str, set[str]] = defaultdict(set)
    for task, text in task_texts.items():
        for pattern in _PATTERNS:
            for match in pattern.findall(text):
                term = match.strip()
                if len(term) >= 4 and _identifier_like(term):
                    index[term.lower()].add(task)
    return dict(index)


def task_specific_hits(edit: Edit, index: Mapping[str, set[str]], *, n_tasks: int,
                       max_share: float = 0.25, allow: frozenset[str] = frozenset()) -> list[str]:
    """Terms of the edit that occur in at most ``max_share`` of the training tasks."""
    limit = max(1, int(n_tasks * max_share))
    text = edit.text().lower()
    hits = []
    for term, tasks in index.items():
        if term in allow or len(tasks) > limit:
            continue
        if re.search(rf"(?<![\w]){re.escape(term)}(?![\w])", text):
            hits.append(f"{term} ({', '.join(sorted(tasks))})")
    return sorted(hits)


async def judge(ask: Ask, edit: Edit) -> tuple[str, str]:
    """Return ``(verdict, reason)``; an unparsable reply counts as task-specific."""
    shown = json.dumps({"op": edit.op, "skill": edit.skill, "description": edit.description,
                        "body": edit.body, "reason": edit.reason}, ensure_ascii=False, indent=1)
    reply = await ask(JUDGE_PROMPT.format(guide=AUTHORING_GUIDE, edit=shown))
    match = re.search(r"\{.*\}", reply, flags=re.S)
    try:
        value = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        value = {}
    verdict = value.get("verdict") if isinstance(value, dict) else None
    if verdict not in {"general", "task_specific"}:
        return "task_specific", f"unparsable judge reply: {reply[:200]!r}"
    return verdict, str(value.get("reason", ""))


async def screen(edit: Edit, *, ask: Ask, index: Mapping[str, set[str]], n_tasks: int,
                 allow: frozenset[str] = frozenset()) -> ScreenResult:
    """Retirements need no screening: they remove text, they cannot overfit it."""
    if edit.op == "retire":
        return ScreenResult(True, (), "general", "retirement")
    hits = task_specific_hits(edit, index, n_tasks=n_tasks, allow=allow)
    if hits:
        return ScreenResult(False, tuple(hits), "not_judged", "names task-specific terms")
    verdict, reason = await judge(ask, edit)
    return ScreenResult(verdict == "general", (), verdict, reason)


__all__ = ["ScreenResult", "judge", "screen", "task_specific_hits", "term_index"]
