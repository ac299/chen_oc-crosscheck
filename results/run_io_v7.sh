#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code_v7.txt 1
echo "IO V7 DONE" >> results/batch.log
