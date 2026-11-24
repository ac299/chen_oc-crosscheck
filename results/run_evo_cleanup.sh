#!/usr/bin/env bash
# Second pass over the EvoCodeBench plan: reruns entries that have no record yet
# (e.g. the duo@s2 r1 run whose grading step broke while run_one.sh was edited).
cd "$(dirname "$0")/.."
until grep -q 'EVO2B DONE' results/batch.log; do sleep 60; done
scripts/batch.sh plans/evocodebench2.txt 3
echo "EVO2C DONE" >> results/batch.log
