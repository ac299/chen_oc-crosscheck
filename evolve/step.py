"""Container-side steps of the skill evolution loop (evolve/driver.py calls them).

Every step that touches the library or calls a model runs here, inside the
Linux container, because OpenCollab cannot run on the Windows host. The
provider configuration arrives on stdin exactly as in scripts/run_agent.py.

  python evolve/step.py init     --lib DIR
  python evolve/step.py snapshot --lib DIR --dest DIR
  python evolve/step.py reflect  --lib DIR --method M --tasks a,b --out FILE
  python evolve/step.py oneshot  --lib DIR --tasks a,b --out FILE
  python evolve/step.py apply    --lib DIR --proposals FILE --index I --out FILE
  python evolve/step.py revert   --lib DIR --proposals FILE --index I --prior STATUS --reason R
  python evolve/step.py status   --lib DIR --skill S --to STATUS --reason R
  python evolve/step.py decide   --base M --cand M --tasks a,b --out FILE
  python evolve/step.py nominate --lib DIR --method M --tasks a,b --out FILE
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from opencollab.adapters.skills.evolving import SkillLibrary
from opencollab.adapters.skills.evolving.evidence import RunOutcome, skills_used
from opencollab.adapters.skills.evolving.gate import decide
from opencollab.adapters.skills.evolving.lifecycle import nominate, usage
from opencollab.adapters.skills.evolving.reflector import (
    AUTHORING_GUIDE,
    Edit,
    TriedEdit,
    apply_edit,
    parse_edits,
    propose,
    revert_edit,
)
from opencollab.adapters.skills.evolving.screen import screen, term_index

ROOT = Path("/kaohe/oc-crosscheck")
RUNS = ROOT / "results" / "runs.jsonl"
RAW = ROOT / "results" / "raw"
TASK_ROOTS = [ROOT / "tasks_bcb"]
CFG = Path("/run/oc-config/oc.env")
REFLECT_BUDGET = 400_000
TEST_PY = os.environ.get("XC_TEST_PYTHON", "/env/venv/bin/python")
_ASK_LOG: list[dict] = []

ONESHOT_PROMPT = """\
You maintain a library of skills (reusable instructions) for a coding agent. The agent will solve
tasks like the examples below: implement one Python function from a natural-language description.
Without seeing any attempt, write at most {max_edits} skills that would help on tasks of this kind.

{guide}
Reply with one JSON object and nothing else:
{{"analysis": "<short>", "edits": [{{"op": "add", "skill": "<lowercase-name>",
  "description": "<one line: when to use it>", "body": "<markdown>", "reason": "...", "evidence": []}}]}}

# Example tasks
{tasks}
"""


# -- model access --------------------------------------------------------------


def load_config() -> None:
    data = sys.stdin.buffer.read() if not sys.stdin.isatty() else b""
    if data:
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_bytes(data)
        os.chmod(CFG, 0o600)
        os.environ["OPENCOLLAB_CONFIG_FILE"] = str(CFG)


def make_ask():
    from opencollab import OpenCollab

    ws = Path(tempfile.mkdtemp(prefix="evolve-ws-"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    oc = OpenCollab(str(ws))
    _ = oc.configuration
    if CFG.exists():
        CFG.unlink()
    os.environ.pop("OPENCOLLAB_CONFIG_FILE", None)
    # The reflector and the judge must not load the library they are editing.
    os.environ.pop("OPENCOLLAB_SKILLS_DIR", None)

    async def ask(prompt: str) -> str:
        t0 = time.time()
        res = await oc.agent(prompt, tools=[], budget=REFLECT_BUDGET)
        _ASK_LOG.append({"tokens": res.tokens, "seconds": round(time.time() - t0, 1), "status": res.status})
        return res.output if isinstance(res.output, str) else str(res.output)

    return ask


# -- evidence ------------------------------------------------------------------


def task_dir(task: str) -> Path:
    for root in TASK_ROOTS:
        if (root / task).is_dir():
            return root / task
    raise SystemExit(f"unknown task {task}")


def records(method: str, tasks: list[str]) -> list[dict]:
    """Graded records of ``method`` on ``tasks``, reps 0-2.

    Concurrent appends to runs.jsonl from several containers on a Windows bind
    mount can interleave and cut lines, so unparsable lines are skipped and a
    missing (task, rep) falls back to the run's own graded_record.json.
    """
    wanted = set(tasks)
    found: dict[tuple[str, int], dict] = {}
    for line in RUNS.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("method") == method and r.get("task") in wanted and int(r.get("rep", -1)) in range(3):
            found[(r["task"], int(r["rep"]))] = r  # a later record of the same run wins
    safe = method.replace(":", "-").replace("+", "-")
    for task in tasks:
        for rep in range(3):
            if (task, rep) in found:
                continue
            graded = sorted(RAW.glob(f"{task}__{safe}__r{rep}__*/graded_record.json"))
            if graded:
                found[(task, rep)] = json.loads(graded[-1].read_text(encoding="utf-8"))
    return [found[k] for k in sorted(found)]


def hidden_failures(task: str, run_id: str, limit: int = 2500) -> str:
    """Re-run the hidden tests on the exported workspace and keep the short tracebacks."""
    src = RAW / run_id / "workspace"
    if not src.is_dir():
        return "(no workspace)"
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "ws"
        shutil.copytree(src, d)
        shutil.copytree(task_dir(task) / "hidden" / "tests", d / "hidden_tests")
        env = dict(os.environ, PYTHONPATH=str(d), MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
        try:
            out = subprocess.run([TEST_PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line",
                                  "-rf", "hidden_tests"], cwd=d, env=env, capture_output=True, text=True,
                                 timeout=180).stdout
        except subprocess.TimeoutExpired:
            return "hidden tests timed out"
    return out[-limit:]


def outcomes(method: str, tasks: list[str], *, evidence: bool) -> list[RunOutcome]:
    result = []
    for r in records(method, tasks):
        run = RAW / r["run_id"]
        details = {}
        if evidence:
            details = {
                "task description": (task_dir(r["task"]) / "task.md").read_text(encoding="utf-8")[:2500],
                "agent final message": str(r.get("output") or "")[:1200],
                "final diff": (run / "final.diff").read_text(encoding="utf-8")[:2500]
                if (run / "final.diff").is_file() else "",
                "hidden test result": r["grade"].get("tail", "") if r.get("grade") else "not graded",
            }
            if not (r.get("grade") or {}).get("resolved"):
                details["hidden test failures"] = hidden_failures(r["task"], r["run_id"])
        result.append(RunOutcome(
            task=r["task"], rep=int(r["rep"]), resolved=bool((r.get("grade") or {}).get("resolved")),
            run_id=r["run_id"], tokens=r.get("tokens"), seconds=r.get("seconds"),
            skills_used=_run_skills(run / "artifacts"),
            details=details,
        ))
    return result


def _run_skills(artifacts: Path) -> tuple[str, ...]:
    """Skills loaded by any session of the run (workflows write one trajectory per session)."""
    names: list[str] = []
    for path in sorted(artifacts.glob("**/*.jsonl")):
        names.extend(skills_used(path))
    return tuple(names)


def train_index(tasks: list[str]) -> dict[str, set[str]]:
    """Identifiers and literals of the training tasks, from their description, hidden tests and reference."""
    texts = {}
    for t in tasks:
        d = task_dir(t)
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        hidden = "\n".join(p.read_text(encoding="utf-8") for p in (d / "hidden").rglob("*.py"))
        texts[t] = "\n".join([(d / "task.md").read_text(encoding="utf-8"), hidden, meta.get("gold_body", "")])
    return term_index(texts)


# -- steps ---------------------------------------------------------------------


async def screened(edits: list[Edit], tasks: list[str], ask) -> list[dict]:
    index = train_index(tasks)
    items = []
    for e in edits:
        s = await screen(e, ask=ask, index=index, n_tasks=len(tasks))
        items.append({"edit": e.raw | {"op": e.op, "skill": e.skill}, "screen": {
            "passed": s.passed, "hits": list(s.hits), "verdict": s.verdict, "reason": s.reason}})
    return items


def cmd_reflect(a) -> dict:
    lib = SkillLibrary(a.lib)
    tasks = a.tasks.split(",")
    runs = outcomes(a.method, tasks, evidence=True)
    if len(runs) != len(tasks) * a.reps:
        raise SystemExit(f"expected {len(tasks) * a.reps} runs of {a.method}, found {len(runs)}")
    tried = [TriedEdit(**t) for t in json.loads(Path(a.tried).read_text(encoding="utf-8"))] if a.tried else []
    ask = make_ask()
    edits, problems, reply = asyncio.run(propose(ask, lib, runs, max_edits=a.max_edits, tried=tried))
    items = asyncio.run(screened(edits, tasks, ask))
    return {"method": a.method, "runs": [r.run_id for r in runs], "reply": reply, "problems": problems,
            "proposals": items, "model_calls": _ASK_LOG, "screen_version": SCREEN_VERSION,
            "tried": [t.__dict__ for t in tried]}


SCREEN_VERSION = 2  # v1 rejected plain English words as task-specific (round 1 of the first run)


def cmd_rescreen(a) -> dict:
    """Screen the proposals of an existing reflect output again; the old result is kept as ``screen_v1``."""
    path = Path(a.proposals)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("screen_version") == SCREEN_VERSION:
        return {"rescreened": 0}
    lib = SkillLibrary(a.lib)
    edits, problems = parse_edits(json.dumps({"edits": [p["edit"] for p in data["proposals"]]}), lib,
                                  max_edits=len(data["proposals"]))
    if problems:
        raise SystemExit(f"proposals no longer parse: {problems}")
    fresh = asyncio.run(screened(edits, a.tasks.split(","), make_ask()))
    for old, new in zip(data["proposals"], fresh):
        old["screen_v1"] = old["screen"]
        old["screen"] = new["screen"]
    data["screen_version"] = SCREEN_VERSION
    data.setdefault("model_calls", []).extend(_ASK_LOG)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"rescreened": len(fresh), "passed": [p["screen"]["passed"] for p in data["proposals"]]}


def cmd_oneshot(a) -> dict:
    lib = SkillLibrary(a.lib)
    tasks = a.tasks.split(",")
    shown = "\n\n".join(f"## Example {i + 1}\n" + (task_dir(t) / "task.md").read_text(encoding="utf-8")[:2000]
                        for i, t in enumerate(tasks))
    ask = make_ask()
    reply = asyncio.run(ask(ONESHOT_PROMPT.format(max_edits=a.max_edits, guide=AUTHORING_GUIDE, tasks=shown)))
    edits, problems = parse_edits(reply, lib, max_edits=a.max_edits)
    items = asyncio.run(screened(edits, tasks, ask))
    return {"reply": reply, "problems": problems, "proposals": items, "model_calls": _ASK_LOG}


def _edit(a) -> Edit:
    item = json.loads(Path(a.proposals).read_text(encoding="utf-8"))["proposals"][a.index]["edit"]
    lib = SkillLibrary(a.lib)
    edits, problems = parse_edits(json.dumps({"edits": [item]}), lib, max_edits=1)
    if not edits:
        raise SystemExit(f"edit no longer applies: {problems}")
    return edits[0]


def cmd_apply(a) -> dict:
    lib = SkillLibrary(a.lib)
    edit = _edit(a)
    prior = apply_edit(lib, edit)
    lib.log({"op": "apply", "edit": edit.raw, "prior": prior, "source": a.proposals})
    return {"prior": prior, "skill": edit.skill, "op": edit.op}


def cmd_revert(a) -> dict:
    lib = SkillLibrary(a.lib)
    edit = _edit_for_revert(a, lib)
    revert_edit(lib, edit, a.prior, reason=a.reason)
    lib.log({"op": "revert", "edit": edit.raw, "reason": a.reason})
    return {"reverted": edit.skill}


def _edit_for_revert(a, lib: SkillLibrary) -> Edit:
    item = json.loads(Path(a.proposals).read_text(encoding="utf-8"))["proposals"][a.index]["edit"]
    return Edit(op=item["op"], skill=item["skill"], reason=str(item.get("reason", "")), evidence=(), raw=item)


def cmd_status(a) -> dict:
    lib = SkillLibrary(a.lib)
    lib.set_status(a.skill, a.to, reason=a.reason)
    lib.log({"op": "status", "skill": a.skill, "to": a.to, "reason": a.reason})
    return {"skill": a.skill, "status": a.to}


def cmd_decide(a) -> dict:
    tasks = a.tasks.split(",")
    base, cand = outcomes(a.base, tasks, evidence=False), outcomes(a.cand, tasks, evidence=False)
    d = decide(base, cand, min_margin=a.min_margin)
    rate = lambda xs: round(sum(o.resolved for o in xs) / len(xs), 4) if xs else None  # noqa: E731
    return {"accept": d.accept, "wins": d.wins, "losses": d.losses, "pairs": d.pairs, "p": round(d.p_value, 4),
            "reason": d.reason, "base": {"method": a.base, "n": len(base), "rate": rate(base)},
            "cand": {"method": a.cand, "n": len(cand), "rate": rate(cand),
                     "skills_loaded_runs": sum(bool(o.skills_used) for o in cand)}}


def cmd_nominate(a) -> dict:
    lib = SkillLibrary(a.lib)
    runs = outcomes(a.method, a.tasks.split(","), evidence=False)
    return {"usage": [u.__dict__ for u in usage(lib, runs)],
            "nominations": [n.__dict__ for n in nominate(lib, runs)]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    for flag in ("--lib", "--dest", "--method", "--tasks", "--out", "--proposals", "--prior", "--reason",
                 "--skill", "--to", "--base", "--cand", "--tried"):
        ap.add_argument(flag)
    ap.add_argument("--index", type=int)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--max-edits", type=int, default=2)
    ap.add_argument("--min-margin", type=int, default=1)
    a = ap.parse_args()
    load_config()
    if a.cmd == "init":
        SkillLibrary.create(a.lib)
        result = {"created": a.lib}
    elif a.cmd == "snapshot":
        result = {"snapshot": str(SkillLibrary(a.lib).snapshot(a.dest))}
    else:
        result = globals()[f"cmd_{a.cmd}"](a)
    text = json.dumps(result, ensure_ascii=False, indent=1, default=str)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    # One JSON line for the driver; long fields stay in --out only (never cut a JSON string).
    summary = {k: v for k, v in result.items() if k not in {"reply", "proposals", "tried", "model_calls"}}
    print(json.dumps(summary, default=str))


if __name__ == "__main__":
    main()
