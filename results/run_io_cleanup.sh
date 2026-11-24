#!/usr/bin/env bash
# Rerun IO2Code v5 entries that still have no record (io_extra_trailingzeros r1 broke
# in its grading step while run_one.sh was edited).
cd "$(dirname "$0")/.."
until grep -q 'IO V4B DONE' results/batch.log; do sleep 60; done
scripts/batch.sh plans/io2code_v5.txt 1
echo "IO V5C DONE" >> results/batch.log
