"""Host-side driver of the skill evolution loop (Windows host, Python >= 3.8).

Runs agent batches through scripts/batch.sh (one isolated container per run)
and every library or model step through evolve/step.py in a container. All
progress is kept in evolve/state.json, so an interrupted loop resumes where it
stopped; finished runs are skipped by batch.sh itself.

  python evolve/driver.py evolve      # rounds of reflect -> screen -> gate -> lifecycle
  python evolve/driver.py oneshot     # the one-shot library used as a control
  python evolve/driver.py test        # final comparison on the test split
  python evolve/driver.py status

Executor: the Single2 agent ("single"). Splits (docs/skill-evolution-protocol.md):
train = eligible tasks 1-13, validation = 34-53, test = 14-33 of the seeded order.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

P = Path(__file__).resolve().parent.parent          # oc-crosscheck
K = P.parent                                       # kaohe
EV = P / "evolve"
STATE = EV / "state.json"
LIB = P / "skills_libs" / "evolved"
SNAP = P / "skills_libs" / "snap"
ENV_FILE = K / "vendor" / "OpenCollab" / "configs" / ".env"   # passed on stdin, never read here
KWIN = "D:/VMWareMachine2/mywork/kaohe"

ORDER = ["b_509", "b_346", "b_917", "b_785", "b_553", "b_1077", "b_988", "b_771", "b_1040", "b_870", "b_424",
         "b_857", "b_587", "b_655", "b_19", "b_752", "b_854", "b_199", "b_999", "b_723", "b_1013", "b_211",
         "b_326", "b_928", "b_971", "b_765", "b_458", "b_341", "b_409", "b_1008", "b_914", "b_530", "b_678",
         "b_324", "b_162", "b_955", "b_401", "b_461", "b_184", "b_267", "b_915", "b_92", "b_906", "b_1015",
         "b_177", "b_445", "b_990", "b_969", "b_1124", "b_845", "b_310", "b_15", "b_526"]
TRAIN, TEST, VAL = ORDER[:13], ORDER[13:33], ORDER[33:53]
REPS = 3
EXECUTOR = "single"
ROUNDS = 3
MAX_EDITS = 2
JOBS = int(os.environ.get("EVOLVE_JOBS", "4"))
ABLATE_EVERY = 2


# -- plumbing ------------------------------------------------------------------


def log(msg: str) -> None:
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with (EV / "driver.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"rounds": [], "current": None, "events": []}


def save_state(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(STATE))


def step(*args: str, model: bool = False) -> dict:
    """Run evolve/step.py in a container; ``model`` passes the provider config on stdin."""
    cmd = ["docker", "run", "--rm", "-i",
           "-v", f"{KWIN}:/kaohe",
           "-v", f"{KWIN}/vendor/OpenCollab-skills:/kaohe/vendor/OpenCollab:ro",
           "--tmpfs", "/kaohe/vendor/OpenCollab/configs",
           "-v", "oc-venv:/venv:ro", "-v", "xc-env-bcb:/env:ro", "-v", "oc-pythons:/pythons:ro",
           "-v", "oc-hf-cache:/hf", "-e", "HF_HOME=/hf", "-e", "MPLBACKEND=Agg",
           "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "XC_TEST_PYTHON=/env/venv/bin/python",
           "-w", "/kaohe/oc-crosscheck", "oc-crosscheck:dev",
           "/venv/bin/python", "evolve/step.py", *args]
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    stdin = ENV_FILE.open("rb") if model else subprocess.DEVNULL
    try:
        out = subprocess.run(cmd, stdin=stdin, capture_output=True, env=env, timeout=3600)
    finally:
        if model:
            stdin.close()
    text = out.stdout.decode("utf-8", "replace").strip()
    if out.returncode != 0:
        raise SystemExit(f"step {args[0]} failed:\n{out.stderr.decode('utf-8', 'replace')[-3000:]}")
    return json.loads(text.splitlines()[-1])


def cpath(p: Path) -> str:
    """Path of a host file as the container sees it."""
    return "/kaohe/" + p.resolve().relative_to(K.resolve()).as_posix()


def run_batch(method: str, tasks: list, lib: Path = None, name: str = "") -> None:
    plan = EV / "plans" / f"{name or method.replace(':', '-').replace('+', '_')}.txt"
    plan.parent.mkdir(exist_ok=True)
    plan.write_text("".join(f"{t} {method} {r}\n" for t in tasks for r in range(REPS)), encoding="utf-8")
    env = dict(os.environ)
    if lib is not None:
        env["SKILLS_LIB"] = str(lib)
        env["SKILLS_TAG"] = lib.name
    log(f"batch {method} on {len(tasks)} tasks x {REPS} (lib={lib.name if lib else '-'})")
    bash = shutil.which("bash") or ""
    if "Git" not in bash:  # WindowsApps\bash.exe would start WSL instead of Git Bash
        raise SystemExit(f"run the driver from Git Bash (bash resolves to {bash!r})")
    subprocess.run([bash, "scripts/batch.sh", plan.relative_to(P).as_posix(), str(JOBS)], cwd=P, env=env,
                   check=True)
    if (P / "results" / "STOP_PROVIDER").exists():
        raise SystemExit("provider balance exhausted (results/STOP_PROVIDER)")
    # Parallel appends to runs.jsonl can cut lines on the Windows bind mount;
    # every run also keeps graded_record.json, so restore lost records now.
    out = subprocess.run([sys.executable, "scripts/reconcile_runs.py", "--apply"], cwd=P, capture_output=True,
                         text=True, check=True).stdout
    log("reconcile: " + out.strip().splitlines()[0])


def snapshot(tag: str) -> Path:
    dest = SNAP / tag
    if not dest.exists():
        step("snapshot", "--lib", cpath(LIB), "--dest", cpath(dest))
    return dest


def method_for(tag: str) -> str:
    return EXECUTOR if tag == "none" else f"{EXECUTOR}+skills-{tag}"


def run_with(tag: str, tasks: list) -> str:
    method = method_for(tag)
    run_batch(method, tasks, None if tag == "none" else SNAP / tag, name=f"{method.replace('+', '_')}_{len(tasks)}")
    return method


def gate(base_tag: str, cand_tag: str, tasks: list, label: str) -> dict:
    out = EV / "gates" / f"{label}.json"
    out.parent.mkdir(exist_ok=True)
    return step("decide", "--base", method_for(base_tag), "--cand", method_for(cand_tag),
                "--tasks", ",".join(tasks), "--out", cpath(out))


# -- evolution -----------------------------------------------------------------


def round_label(state: dict, rnd: int) -> str:
    """``r<N>`` plus a letter for a restarted round, so its tags never reuse an aborted attempt's runs."""
    return f"r{rnd}{state.get('attempts', {}).get(str(rnd), '')}"


def tried_edits(state: dict) -> list:
    """Every earlier edit that was not kept, with where and why it stopped (aggregate numbers only)."""
    tried = []
    for rec in state["rounds"]:
        prop = json.loads((EV / "proposals" / f"{rec['label']}.json").read_text(encoding="utf-8"))["proposals"]
        for e in rec["edits"]:
            if e.get("result") == "accepted":
                continue
            item = prop[e["index"]]["edit"]
            if e.get("result") == "screened out":
                outcome, reason = "screened out", e["screen"]["reason"]
            else:
                g = e["gate"]
                outcome = "rejected by gate"
                reason = (f"on held-out tasks the library with this edit resolved {g['cand']['rate']:.0%} of runs "
                          f"vs {g['base']['rate']:.0%} without it ({g['wins']} wins, {g['losses']} losses "
                          f"over {g['pairs']} paired runs); agents loaded it in "
                          f"{g['cand'].get('skills_loaded_runs', '?')} of {g['cand']['n']} runs")
            tried.append({"op": item["op"], "skill": item["skill"], "description": item.get("description", ""),
                          "body": item.get("body", ""), "outcome": outcome, "reason": reason})
    return tried


def evolve() -> None:
    state = load_state()
    if not (LIB / "library.json").exists():
        step("init", "--lib", cpath(LIB))
    if state["current"] is None:
        # Round 1 starts from the empty library, i.e. plain Single2: its train runs already exist.
        state["current"] = "none"
        save_state(state)
    # Count idle rounds from the saved state: a restarted driver must not reset the stop rule.
    idle = 0
    for done in state["rounds"]:
        idle = 0 if any(e.get("result") == "accepted" for e in done["edits"]) else idle + 1
    for rnd in range(len(state["rounds"]) + 1, ROUNDS + 1):
        if idle >= 2:
            log("two rounds without an accepted edit: stop")
            break
        cur = state["current"]
        label = round_label(state, rnd)
        log(f"== round {rnd} ({label}), current library {cur}")
        rec = {"round": rnd, "label": label, "start": cur, "edits": []}
        run_with(cur, TRAIN)
        run_with(cur, VAL)
        prop = EV / "proposals" / f"{label}.json"
        prop.parent.mkdir(exist_ok=True)
        if not prop.exists():
            tried = EV / "proposals" / f"{label}.tried.json"
            tried.write_text(json.dumps(tried_edits(state), ensure_ascii=False, indent=1), encoding="utf-8")
            step("reflect", "--lib", cpath(LIB), "--method", method_for(cur), "--tasks", ",".join(TRAIN),
                 "--out", cpath(prop), "--max-edits", str(MAX_EDITS), "--tried", cpath(tried), model=True)
        step("rescreen", "--lib", cpath(LIB), "--proposals", cpath(prop), "--tasks", ",".join(TRAIN), model=True)
        proposals = json.loads(prop.read_text(encoding="utf-8"))["proposals"]
        log(f"round {rnd}: {len(proposals)} proposals")
        for i, item in enumerate(proposals):
            e = {"index": i, "op": item["edit"]["op"], "skill": item["edit"]["skill"], "screen": item["screen"]}
            rec["edits"].append(e)
            if not item["screen"]["passed"]:
                e["result"] = "screened out"
                log(f"  edit {i} {e['op']} {e['skill']}: screened out ({item['screen']['reason']})")
                continue
            applied = step("apply", "--lib", cpath(LIB), "--proposals", cpath(prop), "--index", str(i))
            tag = f"{label}e{i}"
            snapshot(tag)
            run_with(tag, VAL)
            g = gate(cur, tag, VAL, tag)
            e["gate"] = g
            if g["accept"]:
                e["result"] = "accepted"
                cur = tag
            else:
                e["result"] = "rejected"
                step("revert", "--lib", cpath(LIB), "--proposals", cpath(prop), "--index", str(i),
                     "--prior", applied["prior"], "--reason", f"gate {g['reason']}")
            log(f"  edit {i} {e['op']} {e['skill']}: {e['result']} ({g['reason']})")
        if rnd % ABLATE_EVERY == 0 and cur != "none":
            cur = lifecycle(rnd, cur, rec)
        rec["end"] = cur
        state["rounds"].append(rec)
        state["current"] = cur
        save_state(state)
        idle = 0 if any(e.get("result") == "accepted" for e in rec["edits"]) else idle + 1
        if idle >= 2:
            log("two rounds without an accepted edit: stop")
            break
    final = snapshot("final") if not (SNAP / "final").exists() else SNAP / "final"
    log(f"evolution finished; final library {final}")


def lifecycle(rnd: int, cur: str, rec: dict) -> str:
    out = EV / "gates" / f"r{rnd}-nominate.json"
    step("nominate", "--lib", cpath(LIB), "--method", method_for(cur), "--tasks", ",".join(VAL),
         "--out", cpath(out))
    noms = json.loads(out.read_text(encoding="utf-8"))["nominations"]
    rec["lifecycle"] = []
    for n in noms:
        if n["action"] == "promote":
            step("status", "--lib", cpath(LIB), "--skill", n["skill"], "--to", "active", "--reason", n["reason"])
            rec["lifecycle"].append({"promote": n["skill"]})
            log(f"  promote {n['skill']}: {n['reason']}")
        elif n["action"] == "ablate":
            step("status", "--lib", cpath(LIB), "--skill", n["skill"], "--to", "retired", "--reason", "ablation")
            tag = f"r{rnd}-without-{n['skill']}"
            snapshot(tag)
            run_with(tag, VAL)
            g = gate(cur, tag, VAL, tag)
            keep_retired = g["wins"] >= g["losses"]
            if keep_retired:
                cur = tag
            else:
                step("status", "--lib", cpath(LIB), "--skill", n["skill"], "--to", "active",
                     "--reason", f"ablation lost: {g['reason']}")
            rec["lifecycle"].append({"ablate": n["skill"], "gate": g, "retired": keep_retired})
            log(f"  ablate {n['skill']}: {'retired' if keep_retired else 'kept'} ({g['reason']})")
    return cur


# -- controls and test ---------------------------------------------------------


def oneshot() -> None:
    lib = P / "skills_libs" / "oneshot"
    out = EV / "proposals" / "oneshot.json"
    out.parent.mkdir(exist_ok=True)
    if not (lib / "library.json").exists():
        step("init", "--lib", cpath(lib))
    if not out.exists():
        step("oneshot", "--lib", cpath(lib), "--tasks", ",".join(TRAIN), "--out", cpath(out),
             "--max-edits", str(MAX_EDITS), model=True)
    for i, item in enumerate(json.loads(out.read_text(encoding="utf-8"))["proposals"]):
        # The control gets the same screening as evolved edits but no gate.
        if item["screen"]["passed"]:
            step("apply", "--lib", cpath(lib), "--proposals", cpath(out), "--index", str(i))
    if not (SNAP / "oneshot").exists():
        step("snapshot", "--lib", cpath(lib), "--dest", cpath(SNAP / "oneshot"))
    log("one-shot library ready")


def test() -> None:
    if not (SNAP / "oneshot").exists():
        raise SystemExit("run oneshot first")
    empty = SNAP / "empty"
    if not empty.exists():
        empty.mkdir(parents=True)
    arms = [("single+skills-empty", empty), ("single+skills-oneshot", SNAP / "oneshot")]
    final = LIB
    if (final / "library.json").exists() and json.loads((final / "library.json").read_text(encoding="utf-8"))["skills"]:
        snapshot("final")
        arms += [("single+skills-final", SNAP / "final"), ("duo@s2+skills-final", SNAP / "final"),
                 ("crosscheck:v7@s2+skills-final", SNAP / "final")]
    else:
        # Evolution kept no skill, so "final" would equal "empty" (docs/skill-evolution-protocol.md).
        log("evolved library is empty: final arms skipped")
    for method, lib in arms:
        run_batch(method, TEST, lib, name=f"test_{method.replace(':', '-').replace('+', '_')}")
    log("test runs finished")


def status() -> None:
    state = load_state()
    print(json.dumps(state, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    {"evolve": evolve, "oneshot": oneshot, "test": test, "status": status}[sys.argv[1]]()
