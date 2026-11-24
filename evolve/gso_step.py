"""Container-side steps of skill evolution v2, GSO style (docs/skill-evolution-gso-protocol.md).

  python evolve/gso_step.py guide0 --lib DIR --tasks a,b --out FILE
  python evolve/gso_step.py revise --lib-in DIR --lib DIR --method M --tasks a,b --history FILE --out FILE
  python evolve/gso_step.py decide --base M --cand M --tasks a,b --out FILE

Reuses the v1 helpers in evolve/step.py (records, hidden-test re-runs, model access,
screening). The provider configuration arrives on stdin, as for every model step.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import step as S  # noqa: E402  (v1 helpers)
from guard_pairs import wilcoxon_p  # noqa: E402

from opencollab.adapters.skills.evolving import SkillLibrary  # noqa: E402
from opencollab.adapters.skills.evolving.reflector import Edit, _last_json_object  # noqa: E402
from opencollab.adapters.skills.evolving.screen import screen  # noqa: E402

SKILL = "task-checklist"
DESCRIPTION = ("Use at the start of every task, before writing code: how to write and then check a "
               "short checklist of this task's own requirements")
CONTRAST_METHODS = ("single-sh", "crosscheck:v7@s2", "duo@s2", "team-collab@s2")

META = """\
You write a GUIDE for a coding agent. The agent solves tasks like the examples below: implement one
Python function from a natural-language description, with no tests provided. The agent can run shell
commands and Python in its workspace.

The guide is NOT a list of answers. At the start of every task the agent loads the guide and uses it
to write a short checklist of THIS task's own requirements (what the description and its examples
pin down: return types and shapes, exceptions it names and when, edge cases it mentions, formats
shown in examples), then implements, then checks each checklist item by running a small script, and
fixes what fails. So the guide must say HOW to read a task and build and check such a checklist.

Rules:
- General procedure and library-level conventions only (for example how pandas, matplotlib, subprocess
  or the standard library usually behave). Never name a specific task's functions, column names, file
  names, constants or expected outputs.
- Conditional rules only: say when a rule applies (for example "only if the description names an
  exception, raise exactly that exception"). Do not turn one observation into a rule for every task.
- Steps the agent can actually perform with its tools. Body under 2000 characters, markdown, with
  sections "## When to use", "## Build the checklist", "## Check it", "## Pitfalls".
- The agent must keep the checklist in its own message, not in a repository file.
"""

GUIDE0 = META + """
Write the first version of the guide from the example task descriptions below (no attempts are shown).
Reply with one JSON object and nothing else: {{"body": "<markdown>", "reason": "<short>"}}

# Example tasks
{tasks}
"""

REVISE = META + """
Below is the current guide and evidence from training tasks solved with it. For each task you see
failed runs (the checklist the agent wrote, its final code diff, the hidden-test failures) next to a
run of the SAME task that resolved it (by any agent). Find what the resolved runs checked or did that
the failed runs' checklists missed, recurring across DIFFERENT tasks, and revise the guide so that an
agent following it would build and check that kind of item. Make minimal edits: keep the existing text
and change or add only what the evidence supports.

Earlier guide versions and how they did on held-out tasks (aggregate numbers only):
{history}

Reply with one JSON object and nothing else: {{"body": "<full new markdown body>", "reason": "<short>"}}

# Current guide
{guide}

# Evidence
{evidence}
"""


def _write_lib(path: str, body: str, reason: str) -> None:
    lib = SkillLibrary.create(path)
    lib.add(SKILL, DESCRIPTION, body, evidence=[], reason=reason)
    lib.log({"op": "add", "skill": SKILL, "reason": reason})


async def _screen(body: str, tasks: list[str], ask) -> dict:
    e = Edit(op="add", skill=SKILL, reason="", evidence=(), body=body, description=DESCRIPTION,
             raw={"op": "add", "skill": SKILL, "description": DESCRIPTION, "body": body})
    s = await screen(e, ask=ask, index=S.train_index(tasks), n_tasks=len(tasks))
    return {"passed": s.passed, "hits": list(s.hits), "verdict": s.verdict, "reason": s.reason}


async def _ask_guide(ask, prompt: str) -> tuple[dict | None, str]:
    """Ask once and retry once if the reply has no usable JSON body (v1 round 3 failed on a cut reply)."""
    reply = ""
    base = prompt
    for _ in range(3):
        reply = await ask(prompt)
        value = _last_json_object(reply)
        if value and isinstance(value.get("body"), str) and value["body"].strip():
            n = len(value["body"])
            if n <= 2000:
                return value, reply
            # g0 attempt 1 failed twice on length alone; say the exact numbers.
            prompt = (base + f"\n\nYour previous body had {n} characters; the hard limit is 2000. Reply again with "
                      f"a body of at most 1700 characters: keep every section, cut wording and examples.\n"
                      f"Previous body:\n{value['body']}")
    return None, reply


def cmd_guide0(a) -> dict:
    tasks = a.tasks.split(",")
    shown = "\n\n".join(f"## Example {i + 1}\n" + (S.task_dir(t) / "task.md").read_text(encoding="utf-8")[:2000]
                        for i, t in enumerate(tasks))
    ask = S.make_ask()
    value, reply = asyncio.run(_ask_guide(ask, GUIDE0.format(tasks=shown)))
    if value is None:
        return {"ok": False, "why": "no usable reply", "reply": reply, "model_calls": S._ASK_LOG}
    scr = asyncio.run(_screen(value["body"], tasks, ask))
    if scr["passed"]:
        _write_lib(a.lib, value["body"], str(value.get("reason", "")))
    return {"ok": scr["passed"], "screen": scr, "body": value["body"], "reason": value.get("reason"),
            "reply": reply, "model_calls": S._ASK_LOG}


def _checklist(run_id: str, limit: int = 1500) -> str:
    """The agent's own text messages (where the guide asks it to keep the checklist)."""
    texts = []
    for f in sorted((S.RAW / run_id / "artifacts").glob("*.json")):
        if f.name == "workflow.json":
            continue
        try:
            msgs = json.loads(f.read_text(encoding="utf-8")).get("messages", [])
        except (OSError, ValueError):
            continue
        texts += [str(m.get("content")) for m in msgs if m.get("role") == "assistant" and m.get("content")]
    return "\n---\n".join(texts)[:limit] or "(no text messages)"


def _solution_diff(run_id: str, limit: int = 2000) -> str:
    """The final diff restricted to non-test files, so a CrossCheck run shows only its solution."""
    path = S.RAW / run_id / "final.diff"
    if not path.is_file():
        return ""
    out, keep = [], True
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("diff --git"):
            keep = "test" not in line
        if keep:
            out.append(line)
    return "\n".join(out)[:limit]


def cmd_revise(a) -> dict:
    tasks = a.tasks.split(",")
    cur = S.records(a.method, tasks)
    best = {}
    for m in CONTRAST_METHODS + (a.method,):
        for r in S.records(m, tasks):
            if (r.get("grade") or {}).get("resolved") and r["task"] not in best:
                best[r["task"]] = r
    blocks, used = [], []
    for t in tasks:
        failed = [r for r in cur if r["task"] == t and not (r.get("grade") or {}).get("resolved")]
        if not failed or t not in best:
            continue  # nothing to contrast: all runs resolved, or no agent resolved this task
        f, s = failed[0], best[t]
        used.append({"task": t, "failed": f["run_id"], "resolved": s["run_id"]})
        blocks.append(
            f"## Task {len(blocks) + 1}\n### Description\n"
            + (S.task_dir(t) / "task.md").read_text(encoding="utf-8")[:2000]
            + f"\n### Failed run ({len(failed)} of 3 runs failed)\nChecklist and messages:\n{_checklist(f['run_id'])}\n"
            + f"Final diff:\n{_solution_diff(f['run_id'])}\nHidden-test failures:\n"
            + S.hidden_failures(t, f["run_id"], limit=1500)
            + f"\n### A run that resolved this task\nFinal diff:\n{_solution_diff(s['run_id'])}\n")
    lib_in = SkillLibrary(a.lib_in)
    _, guide = lib_in.read(SKILL)
    history = Path(a.history).read_text(encoding="utf-8") if a.history else "(none)"
    if not blocks:
        return {"ok": False, "why": "no success-vs-failure contrast on the train tasks", "contrasts": used}
    ask = S.make_ask()
    value, reply = asyncio.run(_ask_guide(ask, REVISE.format(history=history, guide=guide,
                                                             evidence="\n\n".join(blocks))))
    if value is None:
        return {"ok": False, "why": "no usable reply", "reply": reply, "contrasts": used, "model_calls": S._ASK_LOG}
    scr = asyncio.run(_screen(value["body"], tasks, ask))
    if scr["passed"]:
        _write_lib(a.lib, value["body"], str(value.get("reason", "")))
    return {"ok": scr["passed"], "screen": scr, "body": value["body"], "reason": value.get("reason"),
            "contrasts": used, "reply": reply, "model_calls": S._ASK_LOG}


def _sign_p(w: int, l: int) -> float:
    n, k = w + l, min(w, l)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def cmd_decide(a) -> dict:
    tasks = a.tasks.split(",")
    frac = lambda r: (r["grade"]["passed"] / r["grade"]["total"]) if r["grade"]["total"] else 0.0  # noqa: E731
    base = {(r["task"], int(r["rep"])): r for r in S.records(a.base, tasks)}
    cand = {(r["task"], int(r["rep"])): r for r in S.records(a.cand, tasks)}
    keys = sorted(set(base) & set(cand))
    d = [frac(cand[k]) - frac(base[k]) for k in keys]
    wins = sum(cand[k]["grade"]["resolved"] and not base[k]["grade"]["resolved"] for k in keys)
    losses = sum(base[k]["grade"]["resolved"] and not cand[k]["grade"]["resolved"] for k in keys)
    mean_diff = sum(d) / len(d) if d else 0.0
    accept = bool(keys) and mean_diff > 0 and wins >= losses
    return {"accept": accept, "pairs": len(keys), "mean_pass_rate_diff": round(mean_diff, 4),
            "pass_rate_up": sum(x > 0 for x in d), "pass_rate_down": sum(x < 0 for x in d),
            "wilcoxon_p": round(wilcoxon_p(d), 4), "wins": wins, "losses": losses,
            "sign_p": round(_sign_p(wins, losses), 4),
            "base": {"method": a.base, "resolved": sum(base[k]["grade"]["resolved"] for k in keys)},
            "cand": {"method": a.cand, "resolved": sum(cand[k]["grade"]["resolved"] for k in keys)}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    for flag in ("--lib", "--lib-in", "--method", "--tasks", "--out", "--history", "--base", "--cand"):
        ap.add_argument(flag)
    a = ap.parse_args()
    S.load_config()
    result = globals()[f"cmd_{a.cmd}"](a)
    if a.out:
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    # The driver reads --out; stdout carries only a one-line marker.
    print(json.dumps({"done": a.cmd, "ok": result.get("ok", result.get("accept"))}))


if __name__ == "__main__":
    main()
