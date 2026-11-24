#!/usr/bin/env bash
cd "$(dirname "$0")/.."
scripts/batch.sh plans/guard2.txt 3
echo "GUARD2 DONE" >> results/batch.log
