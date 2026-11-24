"""Grade an exported run and append it to results/runs.jsonl.

Besides hidden-test grading, for CrossCheck runs it scores the independent
suite the way ExecCritic does (Base-to-Gold): each Test Designer case is run on
the untouched base and on the reference solution. A case is *valid* if it
passes on the reference. This gives the ground truth for every Auditor verdict.
The reference is only used here, after the agents have finished.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from audit import audit_run  # noqa: E402
from grade import _copy_sources, grade_dir  # noqa: E402

from xc import executor as ex  # noqa: E402


def suite_truth(task_dir: Path, files: dict[str, str]) -> dict[str, dict]:
    if not files:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        gold = Path(tmp) / "gold"
        gold.mkdir()
        _copy_sources(task_dir / "repo", gold)
        _copy_sources(task_dir / "reference", gold)
        base = Path(tmp) / "base"
        base.mkdir()
        _copy_sources(task_dir / "repo", base)
        on_gold = ex.run_tests(gold, "", files).cases
        on_base = ex.run_tests(base, "", files).cases
    return {k: {"gold": v, "base": on_base.get(k, "error")} for k, v in on_gold.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    raw = ROOT / "results" / "raw" / args.run_id
    bcb_task = (ROOT / "tasks_bcb" / args.task / "meta.json").exists()
    ce_task = (ROOT / "tasks_ce" / args.task / "meta.json").exists()
    repo_task = bcb_task or ce_task or (ROOT / "tasks_repo" / args.task / "meta.json").exists()
    io_task = (ROOT / "tasks_io" / args.task).is_dir()
    io_test_task = (ROOT / "tasks_io_test" / args.task).is_dir()
    root = ("tasks_bcb" if bcb_task else "tasks_ce" if ce_task else "tasks_repo" if repo_task
            else "tasks_io" if io_task else "tasks_io_test" if io_test_task else "tasks")
    task_dir = ROOT / root / args.task
    rec = json.loads((raw / "record.json").read_text(encoding="utf-8"))
    rec.update(task=args.task, method=args.method, rep=args.rep,
               suite="bigcodebench" if bcb_task else "classeval" if ce_task else "evocodebench" if repo_task
               else "io2code" if io_task else "io2code_test" if io_test_task else "dev")
    if repo_task:
        sys.path.insert(0, str(ROOT / "repobench"))
        from repograde import grade_repo, suite_truth_repo

        rec["grade"] = grade_repo(task_dir, raw / "workspace")
    else:
        rec["grade"] = grade_dir(task_dir, raw / "workspace")
    rec["audit"] = audit_run(raw / "artifacts")

    out = rec.get("output") if isinstance(rec.get("output"), dict) else {}
    report = out.get("report") or {}
    files = report.pop("indep_files", None) or {}
    if files:
        (raw / "indep_tests.json").write_text(json.dumps(files, indent=1), encoding="utf-8")
        truth = suite_truth_repo(task_dir, files) if repo_task else suite_truth(task_dir, files)
        valid = {k for k, v in truth.items() if v["gold"] == "pass"}
        rec["suite_truth"] = {
            "cases": len(truth),
            "valid_on_gold": len(valid),
            "fail_on_base": sum(1 for v in truth.values() if v["base"] != "pass"),
            "base_to_gold": sum(1 for k, v in truth.items() if k in valid and v["base"] != "pass"),
        }
        verdicts = report.get("audit") or {}
        if verdicts:
            rec["auditor"] = {
                "judged": len(verdicts),
                "correct": sum(1 for k, v in verdicts.items() if v["valid"] == (k in valid)),
                "kept_invalid": sum(1 for k, v in verdicts.items() if v["valid"] and k not in valid),
                "dropped_valid": sum(1 for k, v in verdicts.items() if not v["valid"] and k in valid),
            }
    line = json.dumps(rec, default=str, ensure_ascii=False) + "\n"
    # A copy in the run's own folder: one append to runs.jsonl was once lost when
    # three graders appended at the same time on the Windows bind mount.
    # scripts/reconcile_runs.py restores any record missing from runs.jsonl.
    (raw / "graded_record.json").write_text(line, encoding="utf-8")
    with (ROOT / "results" / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(line)
    g = rec["grade"]
    print(json.dumps({"run_id": args.run_id, "status": rec.get("status"), "tokens": rec.get("tokens"),
                      "seconds": rec.get("seconds"), "passed": g["passed"], "total": g["total"],
                      "resolved": g["resolved"], "escapes": rec["audit"]["escape_calls"],
                      "level": report.get("level"), "suite_truth": rec.get("suite_truth"),
                      "auditor": rec.get("auditor")}))


if __name__ == "__main__":
    _ = shutil
    main()
