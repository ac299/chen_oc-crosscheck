#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q 'IO S2 DONE' results/batch.log; do sleep 30; done
scripts/batch.sh plans/io2code_team_s2.txt 3
echo "IO TEAM S2 DONE" >> results/batch.log
scripts/batch.sh plans/dev_s2.txt 3
echo "DEV S2 DONE" >> results/batch.log
