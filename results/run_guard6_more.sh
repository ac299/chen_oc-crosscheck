#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q "GUARD6 DONE" results/batch.log; do sleep 20; done
[ -f results/STOP_PROVIDER ] && exit 0
scripts/batch.sh plans/classeval_duo_guard6_more.txt 3
echo "GUARD6MORE DONE" >> results/batch.log
