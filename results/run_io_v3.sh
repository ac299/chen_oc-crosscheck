#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q 'DEV V3 DONE' results/batch.log; do sleep 30; done
scripts/batch.sh plans/io2code_v3.txt 3
echo "IO V3 DONE" >> results/batch.log
