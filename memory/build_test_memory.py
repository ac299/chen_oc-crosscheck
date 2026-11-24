"""Build a two-layer memory about writing tests, for the v7 Test Designer
(docs/two-layer-memory-protocol.md, "Test memory").

Source: the Test Designer suites of the recorded crosscheck:v7@s2 runs (reps 0-2) on the
train tasks. Only train tasks are used; test tasks (seeded 14-33) are never read.

Step 1, `label` (grading container of one task, with its environment volume at /env and
no model access): run every case of every suite on the task's reference solution and keep,
per case, its source, whether it held, and the failure message:
  /env/venv/bin/python memory/build_test_memory.py label --task b_509
Step 2, `build` (agent container, provider config on stdin):
  /venv/bin/python memory/build_test_memory.py build --out memory/lib_tests
Layer 2: per train task, the task text, up to 3 cases that held on the reference and up to
3 that did not, each with what the reference actually did. Layer 1: per task with wrong
cases, the model states up to 3 lessons about writing tests from a description; one more
call groups them, each group listing its tasks.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/kaohe/oc-crosscheck")
RUNS = ROOT / "results" / "runs.jsonl"
RAW = ROOT / "results" / "raw"
TASKS = ROOT / "tasks_bcb"
LABELS = ROOT / "memory" / "test_labels"
METHOD = "crosscheck:v7@s2"
PYTHON = os.environ.get("XC_TEST_PYTHON", "/env/venv/bin/python")
LABEL = "Tests an earlier Test Designer wrote for it, checked against the reference solution"
PER_KIND = 3

sys.path.insert(0, str(ROOT / "evolve"))
from driver import ORDER as SEEDED  # noqa: E402  (the seeded BigCodeBench order)

TRAIN = SEEDED[:13]  # the only train tasks with recorded v7 suites

LESSONS = """\
Below is a programming task (implement one Python function from a description), and tests that
an earlier test writer wrote for it from the description alone. Each test was then run on the
task's reference solution. Tests marked HELD passed on it; tests marked WRONG failed on it, so
they expected behaviour the task did not ask for. The reference's actual behaviour is shown.

State up to 3 lessons that would help a test writer on OTHER tasks of this kind avoid writing
wrong tests. A lesson is general: a situation and what to do (what to assert, what not to assume).
Do not name this task's function, columns, files, constants or outputs.

Reply with one JSON object and nothing else: {{"lessons": ["...", "..."]}}

# Task
{task}

# Tests
{tests}
"""

MERGE = """\
Below are lessons for writing tests from a task description, written from different tasks, each
tagged with its task id. Many of them make the same point in different words. Group the lessons
by the point they make, and write ONE general lesson per group, listing every task id in the
group. Write at most 8 groups and put the largest groups first. A group needs lessons from at
least 2 different tasks; leave out points made by one task only. Keep each lesson general and
conditional (when it applies, what to assert or not assume), one or two sentences.

Reply with one JSON object and nothing else:
{{"lessons": [{{"text": "...", "tasks": ["<task id>", ...]}}]}}

# Lessons
{lessons}
"""


# ---------------------------------------------------------------- step 1: label

def v7_runs(task: str) -> list[dict]:
    out = []
    for line in RUNS.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("task") == task and r.get("method") == METHOD and int(r.get("rep", 9)) < 3:
            if (RAW / r["run_id"] / "indep_tests.json").is_file():
                out.append(r)
    return sorted(out, key=lambda r: r["rep"])


def gold_tree(task_dir: Path, tree: Path) -> None:
    """The task repository with the reference body put back (same as repograde.suite_truth_repo)."""
    meta = json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
    shutil.copytree(task_dir / "repo", tree, symlinks=True)
    path = tree / meta["completion_file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    body = meta["sample"]["body_position"]
    body = body if isinstance(body, list) else json.loads(body)
    stub = " " * int(meta["sample"]["indent"]) + "raise NotImplementedError"
    idx = lines.index(stub, body[0] - 1)
    lines[idx:idx + 1] = meta["gold_body"].split("\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def functions(text: str) -> dict[str, str]:
    """Source of every top-level and class-level test function, by name."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            found[node.name] = ast.get_source_segment(text, node) or ""
    return found


def helpers(text: str) -> dict[str, str]:
    """Source of every top-level non-test function and fixture, by name."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    return {n.name: ast.get_source_segment(text, n) or "" for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("test")}


def with_helpers(source: str, pool: dict[str, str]) -> str:
    """The test preceded by the helpers and fixtures it names (one level)."""
    used = [src for name, src in pool.items() if re.search(r"\b" + re.escape(name) + r"\b", source)]
    return "\n\n".join(used + [source])


def label(task: str) -> None:
    task_dir = TASKS / task
    rows = []
    for r in v7_runs(task):
        files = json.loads((RAW / r["run_id"] / "indep_tests.json").read_text(encoding="utf-8"))
        pool = {name: src for text in files.values() for name, src in helpers(text).items()}
        sources = {name: with_helpers(src, pool) for text in files.values() for name, src in functions(text).items()}
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "gold"
            gold_tree(task_dir, tree)
            for rel, text in files.items():
                f = tree / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text, encoding="utf-8")
            report = Path(tmp) / "gold.xml"
            env = dict(os.environ, PYTHONPATH=str(tree), PYTHONDONTWRITEBYTECODE="1")
            subprocess.run([PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
                            f"--junitxml={report}", *sorted(files)],
                           cwd=tree, env=env, capture_output=True, text=True, timeout=300)
            if not report.exists():
                continue
            for case in ET.parse(report).getroot().iter("testcase"):
                bad = case.find("failure") if case.find("failure") is not None else case.find("error")
                name = case.get("name", "").split("[")[0]
                rows.append({"run": r["run_id"], "case": f"{case.get('classname', '')}::{case.get('name')}",
                             "held": bad is None and case.find("skipped") is None,
                             "message": ((bad.get("message") or bad.text or "") if bad is not None else "")[:400],
                             "source": sources.get(name, "")})
    LABELS.mkdir(parents=True, exist_ok=True)
    (LABELS / f"{task}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"task": task, "runs": len(v7_runs(task)), "cases": len(rows),
                      "held": sum(x["held"] for x in rows)}))


# ---------------------------------------------------------------- step 2: build

def pick(rows: list, held: bool) -> list:
    """Up to PER_KIND cases of one kind with a source, spread over the runs, distinct sources."""
    chosen, seen = [], set()
    for x in sorted((x for x in rows if x["held"] == held and x["source"]), key=lambda x: (len(x["source"]), x["case"])):
        if x["source"] not in seen and len(chosen) < PER_KIND:
            chosen.append(x)
            seen.add(x["source"])
    return chosen


def render_tests(held: list, wrong: list) -> str:
    # WRONG cases first: the framework cuts each example at MAX_EXAMPLE_CHARS (2,500).
    parts = [f"# WRONG: failed on the reference with: {x['message'].strip()[:300] or 'an error'}\n{x['source']}"
             for x in wrong]
    parts += [f"# HELD on the reference\n{x['source']}" for x in held]
    return "\n\n".join(parts)


def build(out: Path, examples_only: bool = False) -> None:
    sys.path.insert(0, str(ROOT / "memory"))
    from build_memory import last_json, load_config, make_ask

    if not examples_only:
        load_config()
    out.mkdir(parents=True, exist_ok=True)
    examples, per_task = [], []
    for t in TRAIN:
        path = LABELS / f"{t}.json"
        if not path.is_file():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        held, wrong = pick(rows, True), pick(rows, False)
        if not held and not wrong:
            continue
        task = (TASKS / t / "task.md").read_text(encoding="utf-8")
        examples.append({"id": t, "task": task, "solution": render_tests(held, wrong), "label": LABEL})
        if wrong:
            per_task.append((t, task, render_tests(held, wrong)))
    (out / "examples.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in examples),
                                        encoding="utf-8")
    if examples_only:
        print(json.dumps({"examples": len(examples)}))
        return
    ask, calls = make_ask()
    tagged = []
    for t, task, tests in per_task:
        value = last_json(asyncio.run(ask(LESSONS.format(task=task[:3000], tests=tests[:6000]))))
        for lesson in (value or {}).get("lessons", [])[:3]:
            if isinstance(lesson, str) and lesson.strip():
                tagged.append({"task": t, "text": lesson.strip()})
    prompt = MERGE.format(lessons="\n".join(f"- [{x['task']}] {x['text']}" for x in tagged))
    replies, merged = [], {"lessons": []}
    for _ in range(2):
        replies.append(asyncio.run(ask(prompt)))
        value = last_json(replies[-1])
        if value and value.get("lessons"):
            merged = value
            break
    known = {x["task"] for x in tagged}
    insights = [{"text": str(m.get("text", "")).strip(), "tasks": sorted({t for t in m.get("tasks", []) if t in known})}
                for m in merged.get("lessons", []) if str(m.get("text", "")).strip()]
    (out / "insights.json").write_text(json.dumps(insights, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "build_log.json").write_text(json.dumps({
        "train_tasks": TRAIN, "examples": [e["id"] for e in examples], "lesson_tasks": [p[0] for p in per_task],
        "per_task_lessons": tagged, "merge_replies": replies, "model_call_tokens": calls},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"examples": len(examples), "lesson tasks": len(per_task), "lessons": len(tagged),
                      "merged": len(insights), "shown (>=2 tasks)": sum(len(i["tasks"]) >= 2 for i in insights),
                      "tokens": sum(c or 0 for c in calls)}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("label", "build"))
    ap.add_argument("--task")
    ap.add_argument("--out", default="memory/lib_tests")
    ap.add_argument("--examples-only", action="store_true", help="rewrite examples.jsonl and keep the lessons")
    a = ap.parse_args()
    if a.step == "label":
        label(a.task)
    else:
        build(ROOT / a.out, a.examples_only)


if __name__ == "__main__":
    main()
