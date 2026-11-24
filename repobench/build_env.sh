#!/usr/bin/env bash
# Build a CPU-only Python 3.11 environment for one EvoCodeBench project in the
# Docker volume xc-env-<project>. Writes the log to datasets/evocodebench/envlogs/.
#   repobench/build_env.sh <project>
# Exit code 0 = environment built. The project itself is NOT installed (an
# editable install would point at the original source, which still contains the
# reference bodies); tests run with the repository on PYTHONPATH instead.
#
# v2 (2026-11-21): v1 read requirement files with grep, which skipped UTF-16
# files entirely (skfolio installed nothing) and copied the file elsewhere,
# which broke `-r other.txt` includes (scepter). v2 copies the project to a
# writable place, re-encodes every requirements*.txt to UTF-8 in place, drops
# only editable/self references and installs from the original location.
set -uo pipefail
PROJ="$1"
D="D:/VMWareMachine2/mywork/kaohe/oc-crosscheck/datasets/evocodebench"
VOL="xc-env-$(echo "$PROJ" | tr 'A-Z_' 'a-z-')"
LOGDIR="/d/VMWareMachine2/mywork/kaohe/oc-crosscheck/datasets/evocodebench/envlogs"
mkdir -p "$LOGDIR"
docker volume create "$VOL" >/dev/null
MSYS_NO_PATHCONV=1 timeout 1500 docker run --rm \
  -v "$D/src/Source_Code/$PROJ:/proj:ro" \
  -v "$VOL:/env" -v oc-uv-cache:/uv-cache -v oc-pythons:/pythons \
  -e UV_CACHE_DIR=/uv-cache -e UV_PYTHON_INSTALL_DIR=/pythons -e UV_LINK_MODE=copy \
  -e UV_INDEX_STRATEGY=unsafe-best-match \
  -e UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
  -e UV_HTTP_TIMEOUT=300 \
  oc-crosscheck:dev bash -c '
set -e
rm -rf /env/venv
uv venv -q /env/venv --python 3.11
cp -r /proj /tmp/p
python3 - <<PY
from pathlib import Path
import re
for f in Path("/tmp/p").rglob("requirements*.txt"):
    raw = f.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            text = raw.decode(enc)
            if enc != "utf-16" or raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                break
        except UnicodeDecodeError:
            continue
    keep = [l for l in text.splitlines() if not re.match(r"\s*(-e\s|\.\s*$|\./|#)", l)]
    f.write_text("\n".join(keep) + "\n", encoding="utf-8")
PY
req=""
for f in requirements.txt requirements/requirements.txt; do [ -f "/tmp/p/$f" ] && req="/tmp/p/$f" && break; done
pkgs="pytest pytest-timeout"
cd /tmp/p
if [ -n "$req" ]; then
  echo "using $req ($(grep -cv "^\s*$" "$req") lines)"
  uv pip install -q --python /env/venv/bin/python -r "$req" $pkgs
elif [ -f pyproject.toml ] || [ -f setup.py ]; then
  echo "no requirements file; installing declared dependencies only"
  src=pyproject.toml; [ -f pyproject.toml ] || src=setup.py
  uv pip compile -q "$src" -o /tmp/req.txt
  uv pip install -q --python /env/venv/bin/python -r /tmp/req.txt $pkgs
else
  echo "no dependency manifest"; uv pip install -q --python /env/venv/bin/python $pkgs
fi
/env/venv/bin/python -c "import sys, pytest; print(\"python\", sys.version.split()[0], \"pytest\", pytest.__version__)"
' > "$LOGDIR/$PROJ.log" 2>&1
code=$?
echo "exit $code" >> "$LOGDIR/$PROJ.log"
exit $code
