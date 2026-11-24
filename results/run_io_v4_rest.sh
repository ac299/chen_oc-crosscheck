#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q 'IO V5 DONE' results/batch.log; do sleep 30; done
scripts/batch.sh plans/io2code_v4.txt 2
echo "IO V4 REST DONE" >> results/batch.log
