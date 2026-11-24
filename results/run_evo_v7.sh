#!/usr/bin/env bash
cd "$(dirname "$0")/.."
until grep -q 'EVO V6 DONE' results/batch.log; do sleep 60; done
scripts/batch.sh plans/evocodebench_v7.txt 1
echo "EVO V7 DONE" >> results/batch.log
