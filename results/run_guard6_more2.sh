#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/classeval_duo_guard6_more.txt 3
echo "GUARD6MORE2 DONE" >> results/batch.log
