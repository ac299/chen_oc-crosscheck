#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/main.txt 3
scripts/batch.sh plans/team_collab.txt 3
scripts/batch.sh plans/guard.txt 3
echo "ALL PLANS DONE" >> results/batch.log
