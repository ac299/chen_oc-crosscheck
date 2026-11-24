"""Print crosscheck reports from results/runs.jsonl (optionally filtered by run-id substring)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
needle = sys.argv[1] if len(sys.argv) > 1 else ""
for line in (ROOT / "results" / "runs.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    if needle not in r["run_id"]:
        continue
    g = r.get("grade", {})
    print(f"== {r['run_id']}  tokens={r.get('tokens')} s={r.get('seconds')} "
          f"hidden={g.get('passed')}/{g.get('total')} escapes={r.get('audit', {}).get('escape_calls')}")
    o = r.get("output") if isinstance(r.get("output"), dict) else {}
    rep = o.get("report", {})
    if rep:
        print("  level", rep.get("level"), "winner", rep.get("winner"), rep.get("reason"), "reqs", rep.get("requirements"))
        print("  suite", rep.get("suite"))
        print("  L1", rep.get("level1"))
        if "level2" in rep:
            print("  L2", rep.get("level2"), "suspects", rep.get("suspects"))
        if "final_scores" in rep:
            print("  final", rep.get("final_scores"), "repaired", rep.get("repaired"))
    for row in o.get("ledger", []):
        print("    ", row)
