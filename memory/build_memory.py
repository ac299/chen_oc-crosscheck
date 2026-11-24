"""Build the two-layer experience memory from recorded train runs (docs/two-layer-memory-protocol.md).

Runs in a container with vendor/OpenCollab-skills2 mounted at /kaohe/vendor/OpenCollab,
the provider config on stdin, the project at /kaohe/oc-crosscheck:
  /venv/bin/python memory/build_memory.py --out memory/lib
Learning signal: only whether a past run passed. Hidden-test messages are never shown.

Layer 2: one solved example per train task that some recorded run passed.
Layer 1: for each train task with both a passed and a failed run, the model compares the
two solutions and states up to 3 general lessons; a second call merges the lessons of all
tasks into general ones, each listing the tasks it came from. Lessons backed by fewer than
two tasks are kept in the file but never shown (ExperienceMemory.supported).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/kaohe/oc-crosscheck")
RUNS = ROOT / "results" / "runs.jsonl"
RAW = ROOT / "results" / "raw"
TASKS = ROOT / "tasks_bcb"
CFG = Path("/run/oc-config/oc.env")
ORDER = ("single-sh", "single", "duo@s2", "team-collab@s2", "crosscheck:v7@s2")

sys.path.insert(0, str(ROOT / "evolve"))
from driver import ORDER as SEEDED  # noqa: E402  (the seeded BigCodeBench order)

TRAIN = SEEDED[:13] + ["b_720", "b_800", "b_574", "b_123", "b_443", "b_120", "b_1039", "b_208", "b_618", "b_1053",
                       "b_897", "b_964", "b_486", "b_399", "b_1042", "b_93", "b_37", "b_308", "b_89", "b_367"]

COMPARE = """\
Below is a programming task and two attempts at it by a coding agent. Attempt A passed the task's
hidden tests; attempt B did not. You are not told why B failed. Compare the two solutions and state
up to 3 lessons that would help on OTHER tasks of this kind (implement one Python function from a
description). A lesson is general: a situation and what to do. Do not name this task's function,
columns, files, constants or outputs.

Reply with one JSON object and nothing else: {{"lessons": ["...", "..."]}}

# Task
{task}

# Attempt A (passed)
```python
{good}
```

# Attempt B (failed)
```python
{bad}
```
"""

MERGE = """\
Below are lessons written from different programming tasks, each tagged with its task id. Many
of them make the same point in different words (for example several are about empty inputs,
several about returning exactly the promised type, several about raising only the named
exceptions). Group the lessons by the point they make, and write ONE general lesson per group,
listing every task id in the group. Write at most 8 groups and put the largest groups first.
A group needs lessons from at least 2 different tasks; leave out points made by one task only.
Keep each lesson general and conditional (when it applies, what to do), one or two sentences.

Reply with one JSON object and nothing else:
{{"lessons": [{{"text": "...", "tasks": ["<task id>", ...]}}]}}

# Lessons
{lessons}
"""


def load_config() -> None:
    data = sys.stdin.buffer.read() if not sys.stdin.isatty() else b""
    if data:
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_bytes(data)
        os.chmod(CFG, 0o600)
        os.environ["OPENCOLLAB_CONFIG_FILE"] = str(CFG)


def make_ask():
    from opencollab import OpenCollab

    ws = Path(tempfile.mkdtemp(prefix="memory-ws-"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    oc = OpenCollab(str(ws))
    _ = oc.configuration
    if CFG.exists():
        CFG.unlink()
    os.environ.pop("OPENCOLLAB_CONFIG_FILE", None)
    calls = []

    async def ask(prompt: str) -> str:
        # The Single2 prompt asks for a tool call in every reply; this step has no tools.
        res = await oc.agent(prompt, tools=[], budget=200_000,
                             system_prompt="You analyse programming lessons. You have no tools: answer in "
                                           "plain text with the JSON object the user asks for.")
        calls.append(res.tokens)
        return res.output if isinstance(res.output, str) else str(res.output)

    return ask, calls


def last_json(text: str):
    for cand in [*reversed(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)),
                 text[text.find("{"): text.rfind("}") + 1]]:
        try:
            value = json.loads(cand)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


def runs_by_task() -> dict:
    out: dict = {}
    for line in RUNS.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        # Train tasks 54-73 were only ever run by the earlier skill experiments
        # (single-sh+skills-*), so their recorded runs are part of the pool too.
        if r.get("task") in TRAIN and _source(r.get("method", "")) is not None and int(r.get("rep", 9)) < 3:
            out.setdefault(r["task"], []).append(r)
    return out


def solution(run_id: str) -> str | None:
    path = RAW / run_id / "workspace" / "solution.py"
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def _source(method: str) -> str | None:
    """The ORDER entry a recorded method counts as; earlier skill runs count as single-sh+skills."""
    if method in ORDER:
        return method
    return "single-sh+skills" if method.startswith("single-sh+skills") else None


def pick(rows: list, passed: bool):
    for m in ORDER + ("single-sh+skills",):
        for r in sorted((x for x in rows if _source(x["method"]) == m), key=lambda x: (x["method"], x["rep"])):
            if bool((r.get("grade") or {}).get("resolved")) == passed and solution(r["run_id"]):
                return r
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--merge-from", help="reuse the per-task lessons of an earlier build_log.json")
    a = ap.parse_args()
    load_config()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    if a.merge_from:
        merge_only(out, json.loads((ROOT / a.merge_from).read_text(encoding="utf-8")))
        return
    rows = runs_by_task()
    examples, pairs = [], []
    for t in TRAIN:
        good, bad = pick(rows.get(t, []), True), pick(rows.get(t, []), False)
        task = (TASKS / t / "task.md").read_text(encoding="utf-8")
        if good:
            examples.append({"id": t, "task": task, "solution": solution(good["run_id"]), "from_run": good["run_id"]})
        if good and bad:
            pairs.append((t, task, solution(good["run_id"]), solution(bad["run_id"])))
    (out / "examples.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in examples),
                                        encoding="utf-8")
    ask, calls = make_ask()
    tagged = []
    for t, task, good, bad in pairs:
        value = last_json(asyncio.run(ask(COMPARE.format(task=task[:3000], good=good[:3000], bad=bad[:3000]))))
        for lesson in (value or {}).get("lessons", [])[:3]:
            if isinstance(lesson, str) and lesson.strip():
                tagged.append({"task": t, "text": lesson.strip()})
    insights, replies = merge_lessons(ask, tagged)
    (out / "insights.json").write_text(json.dumps(insights, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "build_log.json").write_text(json.dumps({
        "train_tasks": TRAIN, "examples": [e["id"] for e in examples], "pairs": [p[0] for p in pairs],
        "per_task_lessons": tagged, "merge_replies": replies, "model_call_tokens": calls},
        ensure_ascii=False, indent=1), encoding="utf-8")
    shown = [i for i in insights if len(i["tasks"]) >= 2]
    print(json.dumps({"examples": len(examples), "pairs": len(pairs), "lessons": len(tagged),
                      "merged": len(insights), "shown (>=2 tasks)": len(shown)}))


def merge_lessons(ask, tagged: list) -> tuple[list, list]:
    """Group the per-task lessons into general ones; one retry if the reply has no lesson list."""
    prompt = MERGE.format(lessons="\n".join(f"- [{x['task']}] {x['text']}" for x in tagged))
    replies, merged = [], {"lessons": []}
    for _ in range(2):
        replies.append(asyncio.run(ask(prompt)))
        value = last_json(replies[-1])
        if value and value.get("lessons"):
            merged = value
            break
    known = {x["task"] for x in tagged}
    insights = [{"text": str(m.get("text", "")).strip(),
                 "tasks": sorted({t for t in m.get("tasks", []) if t in known})}
                for m in merged.get("lessons", []) if str(m.get("text", "")).strip()]
    return insights, replies


def merge_only(out: Path, log: dict) -> None:
    """Redo only the merge step from the per-task lessons of an earlier build."""
    tagged = log["per_task_lessons"]
    ask, calls = make_ask()
    insights, replies = merge_lessons(ask, tagged)
    (out / "insights.json").write_text(json.dumps(insights, ensure_ascii=False, indent=1), encoding="utf-8")
    log.update(merge_tokens=calls, merge_replies=replies, merged_from="build_log of an earlier build")
    (out / "build_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"merged": len(insights), "shown (>=2 tasks)": sum(len(i["tasks"]) >= 2 for i in insights)}))


if __name__ == "__main__":
    main()
