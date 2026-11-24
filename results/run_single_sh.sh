#!/usr/bin/env bash
cd "$(dirname "$0")/.."
while ps -ef | grep -q "[r]un_one.sh"; do sleep 10; done
scripts/batch.sh plans/single_sh_test.txt 3
echo "SINGLESH TEST DONE" >> results/batch.log
[ -f results/STOP_PROVIDER ] && exit 0
scripts/batch.sh plans/single_sh_dev.txt 3
echo "SINGLESH DEV DONE" >> results/batch.log
