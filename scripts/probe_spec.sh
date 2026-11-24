#!/usr/bin/env bash
# scripts/probe_spec.sh <taskroot> <task>   e.g. tasks_io io_extra_trailingzeros
set -euo pipefail
ROOT="$1"; TASK="$2"
K="D:/VMWareMachine2/mywork/kaohe"; P="$K/oc-crosscheck"
OUT="/d/VMWareMachine2/mywork/kaohe/oc-crosscheck/results/probes"; mkdir -p "$OUT"
MSYS_NO_PATHCONV=1 docker run --rm -i \
  -v "$K/vendor/OpenCollab-upstream:/kaohe/vendor/OpenCollab:ro" --tmpfs /kaohe/vendor/OpenCollab/configs \
  -v "$P/workflows:/kaohe/oc-crosscheck/workflows:ro" -v "$P/xc:/kaohe/oc-crosscheck/xc:ro" \
  -v "$P/scripts:/kaohe/oc-crosscheck/scripts:ro" \
  -v "$P/$ROOT/$TASK/task.md:/task/task.md:ro" -v "$P/$ROOT/$TASK/repo:/task/repo:ro" \
  -v oc-venv:/venv:ro -e PYTHONDONTWRITEBYTECODE=1 -e OPENCOLLAB_MAX_OUTPUT_TOKENS=32768 -w /tmp \
  oc-crosscheck:dev /venv/bin/python /kaohe/oc-crosscheck/scripts/probe_spec.py \
  < /d/VMWareMachine2/mywork/kaohe/vendor/OpenCollab/configs/.env > "$OUT/$TASK.json"
python -c "
import json,sys
d=json.loads(open(sys.argv[1],encoding='utf-8').read().strip().splitlines()[-1])
print(sys.argv[2], d['status'], d['tokens'], 'gate', d.get('summary'))
print('  verified:', d.get('verified'))
print('  ruled out:', [b[:60] for b,_ in d.get('ruled_out',[])][:6])
" "$OUT/$TASK.json" "$TASK"
