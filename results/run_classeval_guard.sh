#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q "GUARD6MORE2 DONE" results/batch.log; do sleep 20; done
[ -f results/STOP_PROVIDER ] && exit 0
scripts/batch.sh plans/classeval_guard.txt 3
echo "CEGUARD DONE" >> results/batch.log
