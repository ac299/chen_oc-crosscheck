"""Turn graded runs into at most a few incremental library edits.

Follows EvoSkill (arXiv 2603.02766: failure analysis proposes a new skill or an
edit) and ACE (2510.04618: small delta edits instead of rewrites, which avoids
context collapse). The reflector sees both resolved and failed runs because
failure-only experience rarely transfers to new tasks (2610.22984).

The model call is injected as ``ask(prompt) -> text`` so the caller decides
which model, budget and environment run the reflector.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Iterable, Sequence

from opencollab.adapters.skills.evolving.evidence import RunOutcome
from opencollab.adapters.skills.evolving.library import MAX_BODY_CHARS, MAX_LOADABLE_SKILLS, SkillLibrary

Ask = Callable[[str], Awaitable[str]]
OPS = ("add", "patch", "retire")
# A patch must keep most of the current text; a rewrite loses detail (ACE).
MIN_KEPT_LINE_SHARE = 0.6

# The authoring guide is the "meta-skill prior" of Library Drift (2605.19576)
# and the guide that GSO keeps (2609.39148).
AUTHORING_GUIDE = f"""\
Rules for a good skill:
- A skill is a reusable procedure for a CLASS of tasks. It states when it applies and what to do.
- Never name a specific task's functions, column names, file names, constants or expected outputs.
  Describe the situation instead (for example "the task does not state the input column names").
- Do not turn one fix for one task into a rule for every task. Every rule must be supported by
  at least two different tasks in the evidence.
- Prefer steps the agent can actually perform with its tools. Keep the body under {MAX_BODY_CHARS} characters.
- Structure the body as: "## When to use", "## Steps", "## Pitfalls".
"""

PROMPT = """\
You maintain a library of skills (reusable instructions) for a coding agent. Each skill is
listed in the agent's context by name and description; the agent loads the body with
`use_skill(name)` when it decides the skill fits.

Below are graded runs of the agent on training tasks with the current library. For each run you
see whether the hidden tests passed, which skills the agent loaded, and evidence about what
happened. Find failure causes that recur across DIFFERENT tasks, and what the resolved runs did
differently. Then propose at most {max_edits} edits to the library.

{guide}
Allowed edits:
- {{"op": "add", "skill": "<lowercase-name>", "description": "<one line: when to use it>",
   "body": "<markdown>", "reason": "...", "evidence": ["<run_id>", ...]}}
- {{"op": "patch", "skill": "<existing name>", "body": "<full new body>", "reason": "...",
   "evidence": [...]}}  Keep the existing text and change one part of it; do not rewrite.
- {{"op": "retire", "skill": "<existing name>", "reason": "...", "evidence": [...]}}
The library may hold at most {max_skills} skills; it holds {count} now.
If the evidence shows no recurring, fixable cause, propose no edit.
{tried_rule}
Reply with one JSON object and nothing else: {{"analysis": "<short>", "edits": [ ... ]}}

# Current library
{library}
{tried}
# Runs
{runs}
"""

TRIED_RULE = """
Some edits were already tried and not kept; they are listed under "Edits already tried". Do not
propose them again, nor a reworded version with the same advice. An edit rejected by the gate made
held-out results worse or no better, so if you still see the same failure cause, state in
"analysis" why your edit differs from the rejected one and how it avoids its effect.
"""


@dataclass(frozen=True)
class TriedEdit:
    """An earlier edit that was not kept, shown so the reflector does not propose it again.

    ``outcome`` says where it stopped ("screened out" or "rejected by gate") and
    ``reason`` why. Only aggregate gate numbers belong here: showing held-out
    tasks would let the reflector fit the gate set.
    """

    op: str
    skill: str
    description: str
    body: str
    outcome: str
    reason: str


@dataclass(frozen=True)
class Edit:
    op: str
    skill: str
    reason: str
    evidence: tuple[str, ...]
    body: str = ""
    description: str = ""
    raw: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def text(self) -> str:
        """The text a generalization check inspects."""
        return f"{self.skill}\n{self.description}\n{self.body}"


def render_library(library: SkillLibrary, outcomes: Iterable[RunOutcome] = ()) -> str:
    uses: dict[str, int] = {}
    for outcome in outcomes:
        for name in set(outcome.skills_used):
            uses[name] = uses.get(name, 0) + 1
    records = library.records()
    parts = []
    for name in library.loadable_names():
        description, body = library.read(name)
        status = records[name].status if name in records else "manual"
        parts.append(f"## {name} ({status}, loaded in {uses.get(name, 0)} runs)\n"
                     f"description: {description}\n\n{body}")
    return "\n\n".join(parts) or "(empty)"


def render_runs(outcomes: Iterable[RunOutcome], *, max_chars_per_run: int = 3000) -> str:
    blocks = []
    for o in sorted(outcomes, key=lambda o: (o.task, o.rep)):
        head = (f"### run {o.run_id} | task {o.task} | rep {o.rep} | "
                f"{'RESOLVED' if o.resolved else 'FAILED'} | skills loaded: {', '.join(o.skills_used) or 'none'}")
        detail = "\n".join(f"{k}:\n{_clip(str(v), max_chars_per_run // 3)}" for k, v in o.details.items())
        blocks.append(f"{head}\n{_clip(detail, max_chars_per_run)}")
    return "\n\n".join(blocks)


def render_tried(tried: Sequence[TriedEdit], *, max_body_chars: int = 1500) -> str:
    if not tried:
        return ""
    parts = ["# Edits already tried"]
    for t in tried:
        parts.append(f"## {t.op} {t.skill}: {t.outcome}\nreason: {t.reason}\n"
                     f"description: {t.description}\n\n{_clip(t.body, max_body_chars)}")
    return "\n\n".join(parts) + "\n"


def build_prompt(library: SkillLibrary, outcomes: list[RunOutcome], *, max_edits: int = 2,
                 tried: Sequence[TriedEdit] = ()) -> str:
    return PROMPT.format(
        max_edits=max_edits,
        guide=AUTHORING_GUIDE,
        max_skills=MAX_LOADABLE_SKILLS,
        count=len(library.loadable_names()),
        library=render_library(library, outcomes),
        tried_rule=TRIED_RULE if tried else "",
        tried=render_tried(tried),
        runs=render_runs(outcomes),
    )


def parse_edits(text: str, library: SkillLibrary, *, max_edits: int = 2) -> tuple[list[Edit], list[str]]:
    """Parse the reply into edits; malformed or inapplicable ones are reported, not raised."""
    problems: list[str] = []
    payload = _last_json_object(text)
    if payload is None:
        return [], ["reply contains no JSON object"]
    edits: list[Edit] = []
    loadable = set(library.loadable_names())
    for item in (payload.get("edits") or [])[:max_edits]:
        if not isinstance(item, dict):
            problems.append(f"not an object: {item!r}"[:200])
            continue
        op, skill = item.get("op"), item.get("skill")
        if op not in OPS or not isinstance(skill, str) or not skill:
            problems.append(f"bad op or skill: {op!r} {skill!r}")
            continue
        edit = Edit(
            op=op, skill=skill, reason=str(item.get("reason", "")),
            evidence=tuple(str(e) for e in item.get("evidence") or ()),
            body=str(item.get("body", "")).strip(), description=str(item.get("description", "")).strip(),
            raw=item,
        )
        problem = _applicability(edit, library, loadable)
        if problem:
            problems.append(f"{op} {skill}: {problem}")
            continue
        edits.append(edit)
    return edits, problems


def apply_edit(library: SkillLibrary, edit: Edit) -> str:
    """Apply an edit and return the skill's prior status for ``revert_edit``."""
    prior = library.records()[edit.skill].status if edit.skill in library.records() else "absent"
    if edit.op == "add":
        library.add(edit.skill, edit.description, edit.body, evidence=list(edit.evidence), reason=edit.reason)
    elif edit.op == "patch":
        library.patch(edit.skill, body=edit.body, description=edit.description or None,
                      evidence=list(edit.evidence), reason=edit.reason)
    else:
        library.retire(edit.skill, reason=edit.reason)
    return prior


def revert_edit(library: SkillLibrary, edit: Edit, prior: str, *, reason: str) -> None:
    """Undo ``apply_edit`` after a rejected gate."""
    if edit.op == "add":
        library.remove(edit.skill, reason=reason)
    elif edit.op == "patch":
        library.rollback(edit.skill, reason=reason)
    else:
        library.set_status(edit.skill, prior, reason=reason)


async def propose(ask: Ask, library: SkillLibrary, outcomes: list[RunOutcome], *,
                  max_edits: int = 2, tried: Sequence[TriedEdit] = ()) -> tuple[list[Edit], list[str], str]:
    """Return ``(edits, problems, raw_reply)``."""
    reply = await ask(build_prompt(library, outcomes, max_edits=max_edits, tried=tried))
    edits, problems = parse_edits(reply, library, max_edits=max_edits)
    return edits, problems, reply


def _applicability(edit: Edit, library: SkillLibrary, loadable: set[str]) -> str | None:
    if edit.op == "add":
        if edit.skill in library.records() or edit.skill in loadable:
            return "skill already exists"
        if not edit.body or not edit.description:
            return "add needs a description and a body"
        if len(loadable) >= MAX_LOADABLE_SKILLS:
            return "library is full"
        return None
    if edit.skill not in loadable:
        return "no such loadable skill"
    if edit.op == "patch":
        if not edit.body:
            return "patch needs a body"
        _, old = library.read(edit.skill)
        if _kept_share(old, edit.body) < MIN_KEPT_LINE_SHARE:
            return f"patch rewrites the skill (keeps under {MIN_KEPT_LINE_SHARE:.0%} of its lines)"
    return None


def _kept_share(old: str, new: str) -> float:
    old_lines = [line.strip() for line in old.splitlines() if line.strip()]
    if not old_lines:
        return 1.0
    new_lines = {line.strip() for line in new.splitlines()}
    return sum(line in new_lines for line in old_lines) / len(old_lines)


def _last_json_object(text: str) -> dict[str, Any] | None:
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    for candidate in [*reversed(fenced), text[text.find("{"): text.rfind("}") + 1]]:
        try:
            value = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit // 2] + "\n...[clipped]...\n" + text[-limit // 2:]


__all__ = [
    "AUTHORING_GUIDE",
    "Edit",
    "TriedEdit",
    "apply_edit",
    "build_prompt",
    "parse_edits",
    "propose",
    "render_library",
    "render_runs",
    "revert_edit",
]
