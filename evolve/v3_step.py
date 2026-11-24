"""Container-side steps of skill evolution v3 (docs/skill-evolution-v3-protocol.md).

  python evolve/v3_step.py mklib   --lib DIR --spec FILE          # write a library from a JSON spec
  python evolve/v3_step.py advise  --task T --method M --prev FILE --out FILE
  python evolve/v3_step.py distill --evidence FILE --lessons FILE --tasks a,b --out FILE

Reuses the v1 helpers in evolve/step.py and the v2 decide step (evolve/gso_step.py).
The provider configuration arrives on stdin for the model steps.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gso_step as G  # noqa: E402
import step as S  # noqa: E402

from opencollab.adapters.skills.evolving import SkillLibrary  # noqa: E402
from opencollab.adapters.skills.evolving.reflector import Edit, _last_json_object  # noqa: E402
from opencollab.adapters.skills.evolving.screen import screen  # noqa: E402

LESSONS = "coding-lessons"
LESSONS_DESC = "General lessons for implementing a function from a description; load together with task-checklist"
TIP = "task-tip"
TIP_DESC = "Advice for THIS task from earlier attempts at it; load it first"

ADVISE = """\
A coding agent attempted the task below and its code failed hidden tests. Write advice for the
agent's NEXT attempt at THIS SAME task: what it got wrong and what to do instead. The advice may be
specific to this task. Do not include the hidden tests or their expected values verbatim; describe
the behaviour the task requires. At most 800 characters.

Reply with one JSON object and nothing else: {{"advice": "<text>"}}

# Task
{task}

# The attempt's final code diff
{diff}

# Hidden-test failures of the attempt
{failures}

# Advice the attempt was given (if any)
{prev}
"""

DISTILL = """\
You maintain a skill called "coding-lessons" for a coding agent that implements one Python function
from a natural-language description (no tests given; it can run code). Below is advice that FIXED a
failed attempt at a training task (the next attempt with that advice passed the hidden tests), for
several different tasks. Distill general lessons that recur across DIFFERENT tasks.

Rules:
- Each lesson is general: a situation and what to do. Never name a specific task's functions, column
  names, file names, constants or expected outputs. Library-level conventions are allowed.
- Each lesson must be supported by advice from AT LEAST 2 different tasks; list them in "tasks".
  Drop anything supported by only one task.
- Conditional wording: say when the lesson applies.
- Keep the current lessons that are still supported; edit minimally.
- At most 8 lessons; all bodies together under 1800 characters.

Reply with one JSON object and nothing else:
{{"lessons": [{{"text": "<one or two sentences>", "tasks": ["<task id>", ...]}}]}}

# Current lessons
{current}

# Effective advice
{evidence}
"""


def cmd_mklib(a) -> dict:
    """``--spec`` is a list of {"lib": dir, "skills": [{name, description, body}]}; existing libs are kept."""
    made = []
    for item in json.loads(Path(a.spec).read_text(encoding="utf-8")):
        if (Path(item["lib"]) / "library.json").exists():
            continue
        lib = SkillLibrary.create(item["lib"])
        for s in item["skills"]:
            lib.add(s["name"], s["description"], s["body"], evidence=[], reason=s.get("reason", "v3"))
        made.append(item["lib"])
    return {"ok": True, "made": made}


async def _advise_one(ask, job: dict) -> dict:
    recs = S.records(job["method"], [job["task"]])
    r = next((x for x in recs if int(x["rep"]) == 0), None)
    if r is None:
        return {"task": job["task"], "ok": False, "why": f"no record of {job['method']}"}
    prompt = ADVISE.format(task=(S.task_dir(job["task"]) / "task.md").read_text(encoding="utf-8")[:2500],
                           diff=G._solution_diff(r["run_id"], 2500),
                           failures=S.hidden_failures(job["task"], r["run_id"], limit=2000),
                           prev=job.get("prev") or "(none)")
    for _ in range(3):
        value = _last_json_object(await ask(prompt))
        if value and isinstance(value.get("advice"), str) and value["advice"].strip():
            text = value["advice"].strip()
            if len(text) <= 800:
                return {"task": job["task"], "ok": True, "advice": text, "from_run": r["run_id"]}
            prompt += f"\n\nYour advice had {len(text)} characters; the limit is 800. Shorten it."
    return {"task": job["task"], "ok": False, "why": "no usable reply", "from_run": r["run_id"]}


def cmd_advise(a) -> dict:
    """``--spec`` is a list of {"task", "method", "prev"}: one advice per failed attempt."""
    jobs = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    ask = S.make_ask()

    async def all_jobs():
        return [await _advise_one(ask, j) for j in jobs]

    return {"ok": True, "advice": asyncio.run(all_jobs()), "model_calls": S._ASK_LOG}


def cmd_distill(a) -> dict:
    evidence = json.loads(Path(a.evidence).read_text(encoding="utf-8"))
    current = json.loads(Path(a.lessons).read_text(encoding="utf-8")) if a.lessons and Path(a.lessons).exists() else []
    shown = "\n\n".join(f"## {e['task']}\nTask (start): {e['task_head']}\nAdvice that fixed it: {e['advice']}"
                        for e in evidence)
    cur = "\n".join(f"- {x['text']} (tasks: {', '.join(x['tasks'])})" for x in current) or "(none)"
    ask = S.make_ask()
    value = None
    for _ in range(3):
        value = _last_json_object(asyncio.run(ask(DISTILL.format(current=cur, evidence=shown))))
        if value and isinstance(value.get("lessons"), list):
            break
        value = None
    if value is None:
        return {"ok": False, "why": "no usable reply", "model_calls": S._ASK_LOG}
    known = {e["task"] for e in evidence}
    kept, dropped = [], []
    for x in value["lessons"]:
        tasks = sorted({t for t in x.get("tasks", []) if t in known})
        (kept if len(tasks) >= 2 and str(x.get("text", "")).strip() else dropped).append(
            {"text": str(x.get("text", "")).strip(), "tasks": tasks})
    body = "## Lessons\n" + "\n".join(f"- {x['text']}" for x in kept)
    result = {"lessons": kept, "dropped_single_task": dropped, "body": body, "model_calls": S._ASK_LOG}
    if not kept:
        return {**result, "ok": False, "why": "no lesson supported by >= 2 tasks"}
    if len(body) > 2000:
        return {**result, "ok": False, "why": f"body {len(body)} > 2000 characters"}
    train = a.tasks.split(",")
    e = Edit(op="add", skill=LESSONS, reason="", evidence=(), body=body, description=LESSONS_DESC,
             raw={"op": "add", "skill": LESSONS, "description": LESSONS_DESC, "body": body})
    s = asyncio.run(screen(e, ask=ask, index=S.train_index(train), n_tasks=len(train)))
    result["screen"] = {"passed": s.passed, "hits": list(s.hits), "verdict": s.verdict, "reason": s.reason}
    return {**result, "ok": s.passed}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    for flag in ("--lib", "--spec", "--task", "--method", "--prev", "--out", "--evidence", "--lessons", "--tasks"):
        ap.add_argument(flag)
    a = ap.parse_args()
    S.load_config()
    result = globals()[f"cmd_{a.cmd}"](a)
    if a.out:
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"done": a.cmd, "ok": result.get("ok")}))


if __name__ == "__main__":
    main()
