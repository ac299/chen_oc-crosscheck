#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code_v5.txt 2
echo "IO V5 DONE" >> results/batch.log
