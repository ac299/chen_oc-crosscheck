#!/usr/bin/env bash
# Resume after the memory-cap pause. Markers are new so earlier waiters are not confused.
cd "$(dirname "$0")/.."
( scripts/batch.sh plans/evocodebench2.txt 3; echo "EVO2B DONE" >> results/batch.log ) &
( scripts/batch.sh plans/io2code_v5.txt 1; echo "IO V5B DONE" >> results/batch.log
  scripts/batch.sh plans/io2code_v6.txt 1; echo "IO V6B DONE" >> results/batch.log
  scripts/batch.sh plans/io2code_v4.txt 1; echo "IO V4B DONE" >> results/batch.log ) &
wait
