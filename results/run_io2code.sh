#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code.txt 3
echo "IO2CODE DONE" >> results/batch.log
