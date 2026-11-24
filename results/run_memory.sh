#!/usr/bin/env bash
cd "$(dirname "$0")/.."
[ -f results/STOP_PROVIDER ] && exit 0
scripts/batch_mem.sh plans/memory_test.txt 1
echo "MEMTEST DONE" >> results/batch.log
