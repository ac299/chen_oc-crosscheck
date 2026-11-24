#!/usr/bin/env bash
cd "$(dirname "$0")/.."
while ps -ef | grep -q "[g]so.py test"; do sleep 20; done
[ -f results/STOP_PROVIDER ] && exit 0
EVOLVE_JOBS=3 python evolve/v3.py evolve >> evolve/v3.stdout 2>&1
EVOLVE_JOBS=3 python evolve/v3.py test >> evolve/v3.stdout 2>&1
echo "V3 ALL DONE" >> evolve/v3.stdout
