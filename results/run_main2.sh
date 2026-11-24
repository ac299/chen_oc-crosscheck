#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/evocodebench2.txt 3
echo "EVO2 DONE" >> results/batch.log
scripts/batch.sh plans/io2code_v4v5.txt 3
echo "IO V4V5 DONE" >> results/batch.log
