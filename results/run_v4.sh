#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code_v4.txt 2
echo "IO V4 DONE" >> results/batch.log
until grep -q 'EVO DONE' results/batch.log; do sleep 60; done
scripts/batch.sh plans/evocodebench_v4.txt 3
echo "EVO V4 DONE" >> results/batch.log
