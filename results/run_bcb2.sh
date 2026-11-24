#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/bigcodebench2.txt 3
echo "BCB2 DONE" >> results/batch.log
