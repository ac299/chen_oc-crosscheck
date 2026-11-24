#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/bigcodebench.txt 3
echo "BCB DONE" >> results/batch.log
