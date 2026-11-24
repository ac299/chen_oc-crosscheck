#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/classeval_duo_guard6.txt 3
echo "GUARD6 DONE" >> results/batch.log
