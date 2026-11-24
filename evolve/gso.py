"""Host-side driver of skill evolution v2, GSO style (docs/skill-evolution-gso-protocol.md).

  python evolve/gso.py evolve     # g0, then up to two revisions, each gated on validation
  python evolve/gso.py test       # test arms on the 20 test tasks
  python evolve/gso.py status

Run from Git Bash. Agent batches go through scripts/batch.sh (one container per
run); model and library steps go through evolve/gso_step.py in a container.
Progress lives in evolve/gso_state.json, so an interrupted run resumes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import driver as D  # noqa: E402  (v1 plumbing: run_batch, log, paths, splits)

EV, P = D.EV, D.P
STATE = EV / "gso_state.json"
LIBS = P / "skills_libs" / "gso"
OUT = EV / "gso"
EXECUTOR = "single-sh"
CANDIDATES = ("g0", "g1", "g2")


def log(msg: str) -> None:
    D.log("[gso] " + msg)


def load() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"candidates": [], "best": "none"}


def save(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(STATE))


def gstep(*args: str, out: Path, model: bool = False) -> dict:
    """Run evolve/gso_step.py in a container (same mounts as v1 steps); the result is read from ``out``."""
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "run", "--rm", "-i",
           "-v", f"{D.KWIN}:/kaohe",
           "-v", f"{D.KWIN}/vendor/OpenCollab-skills:/kaohe/vendor/OpenCollab:ro",
           "--tmpfs", "/kaohe/vendor/OpenCollab/configs",
           "-v", "oc-venv:/venv:ro", "-v", "xc-env-bcb:/env:ro", "-v", "oc-pythons:/pythons:ro",
           "-v", "oc-hf-cache:/hf", "-e", "HF_HOME=/hf", "-e", "MPLBACKEND=Agg",
           "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "XC_TEST_PYTHON=/env/venv/bin/python",
           "-w", "/kaohe/oc-crosscheck", "oc-crosscheck:dev",
           "/venv/bin/python", "evolve/gso_step.py", *args, "--out", D.cpath(out)]
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    stdin = D.ENV_FILE.open("rb") if model else subprocess.DEVNULL
    try:
        res = subprocess.run(cmd, stdin=stdin, capture_output=True, env=env, timeout=3600)
    finally:
        if model:
            stdin.close()
    if res.returncode != 0 or not out.exists():
        raise SystemExit(f"gso_step {args[0]} failed:\n{res.stderr.decode('utf-8', 'replace')[-3000:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def method(tag: str) -> str:
    return EXECUTOR if tag == "none" else f"{EXECUTOR}+skills-gso-{tag}"


def run(tag: str, tasks: list, name: str) -> None:
    D.run_batch(method(tag), tasks, None if tag == "none" else LIBS / tag, name=f"gso_{tag}_{name}")


def history(state: dict) -> str:
    lines = []
    for c in state["candidates"]:
        g = c.get("gate")
        if g:
            lines.append(f"- {c['tag']}: {'accepted' if g['accept'] else 'rejected'}; mean hidden-test pass-rate "
                         f"change {g['mean_pass_rate_diff']:+.3f} over {g['pairs']} paired held-out runs, "
                         f"resolved {g['cand']['resolved']} vs {g['base']['resolved']} ({g['wins']} wins, "
                         f"{g['losses']} losses)")
        else:
            lines.append(f"- {c['tag']}: {c.get('result')}")
    return "\n".join(lines) or "(none)"


def evolve() -> None:
    state = load()
    run("none", D.VAL, "val")           # baseline single-sh on validation (train runs already exist)
    done = {c["tag"] for c in state["candidates"]}
    for i, tag in enumerate(CANDIDATES):
        if tag in done:
            continue
        lib = LIBS / tag
        if tag == "g0":
            r = gstep("guide0", "--lib", D.cpath(lib), "--tasks", ",".join(D.TRAIN), out=OUT / f"{tag}.json", model=True)
        else:
            prev = state["candidates"][-1]["tag"]
            hist = OUT / f"{tag}.history.txt"
            hist.parent.mkdir(parents=True, exist_ok=True)
            if not hist.exists():
                hist.write_text(history(state), encoding="utf-8")
            r = gstep("revise", "--lib-in", D.cpath(LIBS / prev), "--lib", D.cpath(lib), "--method", method(prev),
                      "--tasks", ",".join(D.TRAIN), "--history", D.cpath(hist), out=OUT / f"{tag}.json", model=True)
        rec = {"tag": tag, "screen": r.get("screen"), "why": r.get("why")}
        if not r.get("ok"):
            rec["result"] = "screened out" if r.get("screen") else f"not produced: {r.get('why')}"
            state["candidates"].append(rec)
            save(state)
            log(f"{tag}: {rec['result']} ({(r.get('screen') or {}).get('reason', '')[:200]})")
            break  # protocol: a screened-out or missing revision ends the loop
        run(tag, D.TRAIN, "train")
        run(tag, D.VAL, "val")
        g = gstep("decide", "--base", method(state["best"]), "--cand", method(tag), "--tasks", ",".join(D.VAL),
                  out=OUT / f"{tag}.gate.json")
        rec.update(gate=g, result="accepted" if g["accept"] else "rejected")
        if g["accept"]:
            state["best"] = tag
        state["candidates"].append(rec)
        save(state)
        log(f"{tag}: {rec['result']} (pass-rate {g['mean_pass_rate_diff']:+.3f}, up {g['pass_rate_up']} / down "
            f"{g['pass_rate_down']}, resolved {g['cand']['resolved']} vs {g['base']['resolved']}, "
            f"{g['wins']}:{g['losses']}); best = {state['best']}")
    log(f"evolution finished; best = {state['best']}")


def test() -> None:
    state = load()
    arms = []
    if (LIBS / "g0").exists():
        arms.append("g0")
    if state["best"] not in ("none", "g0"):
        arms.append(state["best"])
    for tag in arms:
        run(tag, D.TEST, "test")
    log(f"test runs finished for {arms}")


if __name__ == "__main__":
    {"evolve": evolve, "test": test, "status": lambda: print(json.dumps(load(), indent=1, ensure_ascii=False))}[
        sys.argv[1]]()
