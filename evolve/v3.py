"""Host-side driver of skill evolution v3 (docs/skill-evolution-v3-protocol.md).

  python evolve/v3.py evolve    # 3 batches of: per-task refinement -> distillation -> validation gate
  python evolve/v3.py test      # the best library on the 20 test tasks, if it is not g0
  python evolve/v3.py status

Run from Git Bash. Progress lives in evolve/v3_state.json; an interrupted run resumes
(finished agent runs are found by their graded_record.json and never repeated).
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import driver as D  # noqa: E402
import gso as G  # noqa: E402

EV, P = D.EV, D.P
STATE = EV / "v3_state.json"
OUT = EV / "v3"
LIBS = P / "skills_libs" / "v3"
EXECUTOR = "single-sh"
JOBS = int(os.environ.get("EVOLVE_JOBS", "3"))
TRAIN2 = ["b_720", "b_800", "b_574", "b_123", "b_443", "b_120", "b_1039", "b_208", "b_618", "b_1053", "b_897",
          "b_964", "b_486", "b_399", "b_1042", "b_93", "b_37", "b_308", "b_89", "b_367"]
TRAIN = D.TRAIN + TRAIN2
BATCHES = [TRAIN[0:11], TRAIN[11:22], TRAIN[22:33]]

G0_BODY = json.loads((EV / "gso" / "g0.json").read_text(encoding="utf-8"))["body"]
G0_SKILL = {"name": "task-checklist",  # same name and description as v2 (evolve/gso_step.py)
            "description": "Use at the start of every task, before writing code: how to write and then check a "
                           "short checklist of this task's own requirements", "body": G0_BODY}
LESSONS_DESC = ("General lessons for implementing a function from a description; load together with "
                "task-checklist")
TIP_DESC = "Advice for THIS task from earlier attempts at it; load it first"


def log(msg: str) -> None:
    D.log("[v3] " + msg)


def load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"best": {"method": "single-sh+skills-gso-g0", "lessons": []}, "effective": [], "batches": []}


def save(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(STATE))


def vstep(*args: str, out: Path, model: bool = False) -> dict:
    """Run evolve/v3_step.py in a container (the mounts of the v1/v2 steps); result read from ``out``."""
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{D.KWIN}:/kaohe",
           "-v", f"{D.KWIN}/vendor/OpenCollab-skills:/kaohe/vendor/OpenCollab:ro",
           "--tmpfs", "/kaohe/vendor/OpenCollab/configs",
           "-v", "oc-venv:/venv:ro", "-v", "xc-env-bcb:/env:ro", "-v", "oc-pythons:/pythons:ro",
           "-v", "oc-hf-cache:/hf", "-e", "HF_HOME=/hf", "-e", "MPLBACKEND=Agg",
           "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "XC_TEST_PYTHON=/env/venv/bin/python",
           "-w", "/kaohe/oc-crosscheck", "oc-crosscheck:dev",
           "/venv/bin/python", "evolve/v3_step.py", *args, "--out", D.cpath(out)]
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    stdin = D.ENV_FILE.open("rb") if model else subprocess.DEVNULL
    try:
        res = subprocess.run(cmd, stdin=stdin, capture_output=True, env=env, timeout=3600)
    finally:
        if model:
            stdin.close()
    if res.returncode != 0 or not out.exists():
        raise SystemExit(f"v3_step {args[0]} failed:\n{res.stderr.decode('utf-8', 'replace')[-3000:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def lessons_skill(lessons: list) -> dict:
    return {"name": "coding-lessons", "description": LESSONS_DESC,
            "body": "## Lessons\n" + "\n".join(f"- {x['text']}" for x in lessons)}


def skills_of(best: dict) -> list:
    return [G0_SKILL] + ([lessons_skill(best["lessons"])] if best["lessons"] else [])


def make_libs(items: list, name: str) -> None:
    spec = OUT / f"{name}.mklib.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps([{"lib": D.cpath(Path(i["lib"])), "skills": i["skills"]} for i in items],
                               ensure_ascii=False), encoding="utf-8")
    vstep("mklib", "--spec", D.cpath(spec), out=OUT / f"{name}.mklib.out.json")


def graded(task: str, method: str) -> dict | None:
    safe = method.replace(":", "-").replace("+", "-")
    hits = sorted((P / "results" / "raw").glob(f"{task}__{safe}__r0__*/graded_record.json"))
    return json.loads(hits[-1].read_text(encoding="utf-8")) if hits else None


def run_one(task: str, method: str, lib: Path) -> dict:
    done = graded(task, method)
    if done:
        return done
    if (P / "results" / "STOP_PROVIDER").exists():
        raise SystemExit("provider balance exhausted")
    env = dict(os.environ, SKILLS_LIB=str(lib), SKILLS_TAG=f"{lib.parent.name}-{lib.name}")
    bash = D.shutil.which("bash")
    try:
        # No coreutils `timeout` here: from Windows Python it resolves to System32	imeout.exe.
        subprocess.run([bash, "scripts/run_one.sh", task, method, "0"], cwd=P, env=env,
                       capture_output=True, timeout=2400)
    except subprocess.TimeoutExpired:
        pass
    rec = graded(task, method)
    raw = sorted((P / "results" / "raw").glob(f"{task}__{method.replace(':', '-').replace('+', '-')}__r0__*"))
    if raw:
        text = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in raw[-1].rglob("*.json*")
                       if p.is_file() and p.stat().st_size < 5_000_000)
        if "Insufficient Balance" in text or "Error code: 402" in text:
            (P / "results" / "STOP_PROVIDER").write_text(f"provider balance exhausted at {raw[-1]}", encoding="utf-8")
            raise SystemExit("provider balance exhausted")
    return rec or {"grade": {"resolved": False, "passed": 0, "total": 0}, "run_id": None, "missing": True}


def wave(jobs: list) -> dict:
    """Run (task, method, lib) jobs, JOBS at a time; returns {task: record}."""
    out = {}
    with cf.ThreadPoolExecutor(JOBS) as pool:
        futs = {pool.submit(run_one, t, m, l): t for t, m, l in jobs}
        for f in cf.as_completed(futs):
            out[futs[f]] = f.result()
    subprocess.run([sys.executable, "scripts/reconcile_runs.py", "--apply"], cwd=P, capture_output=True)
    return out


def refine(k: int, tasks: list, state: dict) -> None:
    """Stage A for one batch: up to 3 attempts per task, advice revised after each failure."""
    best = state["best"]
    base_lib = LIBS / f"b{k}" / "base"
    make_libs([{"lib": str(base_lib), "skills": skills_of(best)}], f"b{k}-base")
    prev_advice: dict = {}
    pending = list(tasks)
    rec = state["batches"][-1]
    for n in (1, 2, 3):
        method = f"{EXECUTOR}+skills-v3b{k}a{n}"
        if n == 1:
            jobs = [(t, method, base_lib) for t in pending]
        else:
            items = [{"lib": str(LIBS / f"b{k}" / f"a{n}" / t),
                      "skills": skills_of(best) + [{"name": "task-tip", "description": TIP_DESC,
                                                    "body": "## Advice from earlier attempts\n" + prev_advice[t]}]}
                     for t in pending]
            make_libs(items, f"b{k}-a{n}")
            jobs = [(t, method, LIBS / f"b{k}" / f"a{n}" / t) for t in pending]
        log(f"batch {k} attempt {n}: {len(jobs)} tasks")
        results = wave(jobs)
        for t in pending:
            ok = bool(results[t]["grade"]["resolved"])
            if any(x["n"] == n for x in rec["attempts"].get(t, [])):
                continue  # resumed run: already recorded
            rec["attempts"].setdefault(t, []).append({"n": n, "resolved": ok, "run_id": results[t].get("run_id"),
                                                      "advice_used": prev_advice.get(t)})
            if ok and n > 1:
                state["effective"].append({"task": t, "batch": k, "attempt": n, "advice": prev_advice[t],
                                           "task_head": (P / "tasks_bcb" / t / "task.md").read_text(
                                               encoding="utf-8")[:300]})
        save(state)
        pending = [t for t in pending if not results[t]["grade"]["resolved"]]
        if n == 3 or not pending:
            break
        spec = OUT / f"b{k}-advise-a{n}.json"
        spec.write_text(json.dumps([{"task": t, "method": method, "prev": prev_advice.get(t)} for t in pending],
                                   ensure_ascii=False), encoding="utf-8")
        adv = vstep("advise", "--spec", D.cpath(spec), out=OUT / f"b{k}-advise-a{n}.out.json", model=True)
        got = {x["task"]: x["advice"] for x in adv["advice"] if x.get("ok")}
        pending = [t for t in pending if t in got]
        prev_advice.update(got)
        if not pending:
            break


def evolve() -> None:
    state = load()
    for k, tasks in enumerate(BATCHES, start=1):
        if any(b["k"] == k and b.get("done") for b in state["batches"]):
            continue
        if not any(b["k"] == k for b in state["batches"]):
            state["batches"].append({"k": k, "tasks": tasks, "attempts": {}})
            save(state)
        log(f"== batch {k}: {len(tasks)} train tasks, best = {state['best']['method']}")
        refine(k, tasks, state)
        rec = state["batches"][-1]
        ev_file = OUT / f"b{k}-evidence.json"
        ev_file.write_text(json.dumps(state["effective"], ensure_ascii=False, indent=1), encoding="utf-8")
        cur_file = OUT / f"b{k}-current-lessons.json"
        cur_file.write_text(json.dumps(state["best"]["lessons"], ensure_ascii=False), encoding="utf-8")
        log(f"batch {k}: {len(state['effective'])} effective advice so far")
        if len({e['task'] for e in state['effective']}) < 2:
            rec.update(distill={"ok": False, "why": "fewer than 2 tasks with effective advice"}, done=True)
            save(state)
            log(f"batch {k}: not enough effective advice to distill")
            continue
        d = vstep("distill", "--evidence", D.cpath(ev_file), "--lessons", D.cpath(cur_file),
                  "--tasks", ",".join(TRAIN), out=OUT / f"b{k}-distill.json", model=True)
        rec["distill"] = {k2: d.get(k2) for k2 in ("ok", "why", "lessons", "dropped_single_task", "screen")}
        if not d.get("ok"):
            rec["done"] = True
            save(state)
            log(f"batch {k}: distillation not used ({d.get('why') or (d.get('screen') or {}).get('reason', '')[:200]})")
            continue
        cand = {"method": f"{EXECUTOR}+skills-v3L{k}", "lessons": d["lessons"]}
        lib = LIBS / f"L{k}"
        make_libs([{"lib": str(lib), "skills": skills_of(cand)}], f"L{k}")
        D.run_batch(cand["method"], D.VAL, lib, name=f"v3_L{k}_val")
        g = G.gstep("decide", "--base", state["best"]["method"], "--cand", cand["method"], "--tasks",
                    ",".join(D.VAL), out=OUT / f"L{k}.gate.json")
        rec.update(gate=g, done=True)
        if g["accept"]:
            state["best"] = cand
        save(state)
        log(f"batch {k}: L{k} {'accepted' if g['accept'] else 'rejected'} (pass-rate {g['mean_pass_rate_diff']:+.3f}, "
            f"resolved {g['cand']['resolved']} vs {g['base']['resolved']}, {g['wins']}:{g['losses']}); "
            f"best = {state['best']['method']}")
    log(f"evolution finished; best = {state['best']['method']}")


def test() -> None:
    state = load()
    m = state["best"]["method"]
    if m == "single-sh+skills-gso-g0":
        log("best is g0, whose test runs already exist")
        return
    k = m.rsplit("L", 1)[1]
    D.run_batch(m, D.TEST, LIBS / f"L{k}", name=f"v3_L{k}_test")
    log("test runs finished")


if __name__ == "__main__":
    {"evolve": evolve, "test": test, "status": lambda: print(json.dumps(load(), indent=1, ensure_ascii=False)[:8000])}[
        sys.argv[1]]()
