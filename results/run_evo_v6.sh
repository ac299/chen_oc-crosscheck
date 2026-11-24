#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/evocodebench_v6.txt 1
echo "EVO V6 DONE" >> results/batch.log
