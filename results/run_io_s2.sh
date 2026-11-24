#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code_s2.txt 3
echo "IO S2 DONE" >> results/batch.log
