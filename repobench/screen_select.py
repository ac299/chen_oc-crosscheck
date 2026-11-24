"""Seeded eligibility walk and sample selection (see docs/repobench-protocol.md).

python -I repobench/select.py            # host side; drives Docker
Appends every decision to datasets/evocodebench/screen.jsonl and writes the final
choice to datasets/evocodebench/selected.json. Resumable: projects/samples already
in screen.jsonl are not redone.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

SEED = 20261120
TARGET = 10
ROOT = Path(__file__).resolve().parent.parent
DS = ROOT / "datasets" / "evocodebench"
SCREEN = DS / "screen.jsonl"
DS_WIN = "D:/VMWareMachine2/mywork/kaohe/oc-crosscheck/datasets/evocodebench"
RB_WIN = "D:/VMWareMachine2/mywork/kaohe/oc-crosscheck/repobench"


def volume(project: str) -> str:
    return "xc-env-" + project.lower().replace("_", "-")


def log(rec: dict) -> None:
    with SCREEN.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False)[:300], flush=True)


def done() -> dict:
    seen: dict = {"env": {}, "sample": {}}
    if SCREEN.exists():
        for line in SCREEN.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["kind"] == "env":
                seen["env"][r["project"]] = r
            else:
                seen["sample"][r["namespace_key"]] = r
    return seen


def build_env(project: str) -> bool:
    code = subprocess.run(["bash", str(ROOT / "repobench" / "build_env.sh"), project]).returncode
    return code == 0


def check(sample: dict, project: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=DS, encoding="utf-8") as fh:
        json.dump(sample, fh)
        name = Path(fh.name).name
    try:
        proc = subprocess.run(
            ["docker", "run", "--rm", "-v", "oc-hf-cache:/hf", "-e", "HF_HOME=/hf",
             "-v", f"{DS_WIN}/src/Source_Code/{project}:/proj:ro",
             "-v", f"{DS_WIN}/{name}:/sample.json:ro",
             "-v", f"{RB_WIN}:/rb:ro",
             "-v", f"{volume(project)}:/env:ro", "-v", "oc-pythons:/pythons:ro",
             "oc-crosscheck:dev", "/env/venv/bin/python", "-I", "/rb/check_sample.py",
             "/sample.json", "/proj", "/env/venv/bin/python"],
            capture_output=True, text=True, timeout=400,
            env={"MSYS_NO_PATHCONV": "1", **__import__("os").environ},
        )
        line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        return json.loads(line) if line.startswith("{") else {"error": (proc.stderr or proc.stdout)[-400:]}
    except subprocess.TimeoutExpired:
        return {"error": "check timeout"}
    finally:
        (DS / name).unlink(missing_ok=True)


def main() -> None:
    rows = [json.loads(l) for l in (DS / "meta" / "data.jsonl").read_text(encoding="utf-8").splitlines()]
    by_project: dict[str, list[dict]] = {}
    for r in rows:
        by_project.setdefault(r["completion_path"].split("/")[0], []).append(r)
    projects = sorted(by_project)
    random.Random(SEED).shuffle(projects)
    seen = done()
    selected = []
    for project in projects:
        if len(selected) >= TARGET:
            break
        env = seen["env"].get(project)
        if env is None:
            ok = build_env(project)
            env = {"kind": "env", "project": project, "ok": ok}
            log(env)
        if not env["ok"]:
            continue
        samples = sorted(by_project[project], key=lambda r: r["namespace"])
        random.Random(f"{SEED}:{project}").shuffle(samples)
        for s in samples:
            key = f"{project}:{s['namespace']}"
            rec = seen["sample"].get(key)
            if rec is None:
                res = check(s, project)
                gold_ok = res.get("gold", {}).get("failed", 1) == 0 and res.get("gold", {}).get("passed", 0) > 0
                stub_bad = res.get("stub", {}).get("failed", 0) > 0
                rec = {"kind": "sample", "project": project, "namespace_key": key, "result": res,
                       "eligible": bool(gold_ok and stub_bad),
                       "reason": "ok" if gold_ok and stub_bad else ("gold fails" if not gold_ok else "stub passes")}
                log(rec)
            if rec["eligible"]:
                selected.append({"project": project, "namespace": s["namespace"], "sample": s})
                break
    (DS / "selected.json").write_text(json.dumps(selected, indent=1, ensure_ascii=False), encoding="utf-8")
    print("SELECTED", len(selected), [f"{x['project']}:{x['namespace']}" for x in selected], flush=True)
    sys.exit(0 if len(selected) == TARGET else 2)


if __name__ == "__main__":
    main()
