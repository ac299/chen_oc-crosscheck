#!/usr/bin/env bash
# Run a command inside the experiment container.
#   scripts/dk.sh <command...>
# Mounts the kaohe folder at /kaohe. The Linux venv and uv cache live in
# Docker volumes so the Windows .venv in vendor/OpenCollab is never touched.
# configs/.env (API key) is read by OpenCollab inside the container only.
set -euo pipefail
# The kaohe folder. Default: this machine. Override for another machine, e.g.
#   KAOHE=E:/work/kaohe scripts/dk.sh ...   (Windows form; /e/work/kaohe also works)
K="${KAOHE:-D:/VMWareMachine2/mywork/kaohe}"
case "$K" in /?/*) K="$(printf %s "${K:1:1}" | tr a-z A-Z):${K:2}" ;; esac
KAOHE_WIN="$K"
TTY_FLAGS=""
if [ -t 0 ] && [ -t 1 ]; then TTY_FLAGS="-it"; fi
MSYS_NO_PATHCONV=1 exec docker run --rm $TTY_FLAGS \
  -v "${KAOHE_WIN}:/kaohe" \
  -v oc-venv:/venv \
  -v oc-uv-cache:/uv-cache \
  -v oc-work:/work \
  -e OPENCOLLAB_WORKFLOWS_DIR=/kaohe/oc-crosscheck/workflows \
  -e OPENCOLLAB_CONFIG_FILE=/kaohe/vendor/OpenCollab/configs/.env \
  -w /kaohe/oc-crosscheck \
  oc-crosscheck:dev "$@"
