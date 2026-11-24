#!/usr/bin/env bash
cd "$(dirname "$0")/.."
( until grep -q 'EVO V6 DONE' results/batch.log; do sleep 60; done
  scripts/batch.sh plans/evocodebench_v7.txt 1; echo "EVO V7 DONE" >> results/batch.log ) &
( until grep -q 'IO V5C DONE' results/batch.log; do sleep 60; done
  scripts/batch.sh plans/io2code_v7.txt 1; echo "IO V7 DONE" >> results/batch.log ) &
wait
