#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/io2code_test.txt 3
echo "IOTEST DONE" >> results/batch.log
scripts/batch.sh plans/classeval.txt 3
echo "CLASSEVAL DONE" >> results/batch.log
