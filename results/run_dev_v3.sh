#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/dev_v3.txt 3
echo "DEV V3 DONE" >> results/batch.log
