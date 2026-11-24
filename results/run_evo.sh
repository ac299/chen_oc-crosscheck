#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/evocodebench.txt 3
echo "EVO DONE" >> results/batch.log
