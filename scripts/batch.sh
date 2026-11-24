#!/usr/bin/env bash
# Run a plan file of "<task> <method> <rep>" lines, N jobs in parallel.
#   scripts/batch.sh plans/main.txt 3
# Each job is an isolated scripts/run_one.sh; one summary line per run goes to
# results/batch.log. Already-finished (task, method, rep) triples are skipped,
# so the batch can be resumed after an interruption.
set -uo pipefail
PLAN="$1"; JOBS="${2:-3}"
cd "$(dirname "$0")/.."
LOG=results/batch.log
touch results/runs.jsonl "$LOG"
done_keys=$(python -c "
import json
for l in open('results/runs.jsonl', encoding='utf-8'):
    try:
        r = json.loads(l)
    except ValueError:
        continue  # a line cut by concurrent appends; scripts/reconcile_runs.py restores the record
    # every recorded outcome counts, including framework failures; only runs
    # removed from runs.jsonl (provider/infrastructure faults) are run again
    if '__r9__' not in r['run_id']:
        print(r['task'], r['method'], r['rep'])
")
grep -v '^\s*#' "$PLAN" | grep -v '^\s*$' | while read -r t m r; do
  if ! grep -qx "$t $m $r" <<<"$done_keys"; then echo "$t $m $r"; fi
done | xargs -P "$JOBS" -L 1 bash -c '
  # Stop starting new runs once the provider account is out of balance (HTTP 402):
  # in the first IO2Code pass 68 runs were wasted after the balance ran out.
  if [ -f results/STOP_PROVIDER ]; then echo "$(date +%H:%M:%S) $0 $1 $2 SKIPPED (provider stop)" >> results/batch.log; exit 0; fi
  out=$(timeout 2400 scripts/run_one.sh "$0" "$1" "$2" 2>&1 | tail -1)
  echo "$(date +%H:%M:%S) $0 $1 $2 $out" >> results/batch.log
  rid=$(ls -td results/raw/"$0"__* 2>/dev/null | head -1)
  if [ -n "$rid" ] && grep -rqs "Insufficient Balance\|Error code: 402" "$rid"/record.json "$rid"/artifacts/*.jsonl; then
    echo "provider balance exhausted at $rid" > results/STOP_PROVIDER
  fi'
echo "batch finished: $PLAN" >> "$LOG"
