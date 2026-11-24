#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q "SUITE DONE" results/evidence/suite_fix_budget.txt 2>/dev/null; do sleep 20; done
[ -f results/STOP_PROVIDER ] && exit 0
scripts/batch.sh plans/team_shared_test.txt 3
echo "TEAMSHARED DONE" >> results/batch.log
