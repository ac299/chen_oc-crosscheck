#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/bigcodebench3.txt 3
echo "BCB3 DONE" >> results/batch.log
