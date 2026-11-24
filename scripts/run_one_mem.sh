#!/usr/bin/env bash
# Copy of scripts/run_one.sh plus the "+mem-*" methods (made while run_one.sh was in use).
# One experiment run: isolated agent container, then grading container.
#   scripts/run_one.sh <task> <method> <rep>
# <task> is a folder under tasks/ (development set) or tasks_repo/ (EvoCodeBench).
# Output: results/raw/<run_id>/ and one line appended to results/runs.jsonl
set -euo pipefail
TASK="$1"; METHOD="$2"; REP="$3"; BUDGET="${BUDGET:-800000}"
# "<method>+guard" runs the method with the candidate path guard enabled.
case "$METHOD" in *+guard) GUARD=1 ;; esac
# "<method>+skills" runs the method on vendor/OpenCollab-skills with the skill
# library SKILLS_LIB (a host folder, mounted read-only at /skills). A suffix
# "+skills-<tag>" names the library state, so each state is its own method.
case "$METHOD" in *+skills|*+skills-*) SKILLS=1 ;; esac
if [ "${SKILLS:-0}" = "1" ] && [ ! -d "${SKILLS_LIB:-}" ]; then echo "SKILLS_LIB must name a library folder" >&2; exit 2; fi
# The kaohe folder. Default: this machine. Override for another machine, e.g.
#   KAOHE=E:/work/kaohe scripts/run_one_mem.sh ...   (Windows form; /e/work/kaohe also works)
K="${KAOHE:-D:/VMWareMachine2/mywork/kaohe}"
case "$K" in /?/*) K="$(printf %s "${K:1:1}" | tr a-z A-Z):${K:2}" ;; esac
# The same folder in Git Bash form (/d/...), for file tests on the host.
KP="/$(printf %s "${K:0:1}" | tr A-Z a-z)${K:2}"
P="$K/oc-crosscheck"
M_SAFE="${METHOD//:/-}"; M_SAFE="${M_SAFE//+/-}"; RUN_ID="${TASK}__${M_SAFE}__r${REP}__$(date +%s)"
ENV_FILE="$KP/vendor/OpenCollab/configs/.env"
mkdir -p "$KP/oc-crosscheck/results/raw/$RUN_ID"

# Task kind. Repository tasks run with their project's environment volume; the
# agents' `python` resolves to it while OpenCollab itself runs from /venv.
TASKROOT=tasks; EXTRA=(); GRADE_EXTRA=()
if [ -d "$KP/oc-crosscheck/tasks_io/$TASK" ]; then
  TASKROOT=tasks_io; GRADE_EXTRA=(--network none)
elif [ -d "$KP/oc-crosscheck/tasks_io_test/$TASK" ]; then
  # held-out IO2CodeBench test tasks (docs/heldout-test-protocol.md), same format as tasks_io
  TASKROOT=tasks_io_test; GRADE_EXTRA=(--network none)
elif [ -f "$KP/oc-crosscheck/tasks_repo/$TASK/meta.json" ] || \
     [ -f "$KP/oc-crosscheck/tasks_bcb/$TASK/meta.json" ] || \
     [ -f "$KP/oc-crosscheck/tasks_ce/$TASK/meta.json" ]; then
  # tasks_repo: EvoCodeBench; tasks_bcb: BigCodeBench-Hard; tasks_ce: ClassEval (same layout and grader)
  TASKROOT=tasks_repo
  if [ -d "$KP/oc-crosscheck/tasks_bcb/$TASK" ]; then TASKROOT=tasks_bcb; fi
  if [ -d "$KP/oc-crosscheck/tasks_ce/$TASK" ]; then TASKROOT=tasks_ce; fi
  VOL=$(python -c "import json,sys; print(json.load(open(sys.argv[1]))['env_volume'])" \
        "$KP/oc-crosscheck/$TASKROOT/$TASK/meta.json")
  EXTRA=(-v "$VOL:/env:ro" -v oc-pythons:/pythons:ro
         -e PATH=/env/venv/bin:/venv/bin:/usr/local/bin:/usr/bin:/bin
         -e PYTHONPATH=.:src -e XC_TEST_PYTHON=/env/venv/bin/python)
  EXTRA+=(-v oc-hf-cache:/hf -e HF_HOME=/hf -e MPLBACKEND=Agg)
  GRADE_EXTRA=(-v "$VOL:/env:ro" -v oc-pythons:/pythons:ro -v oc-hf-cache:/hf -e HF_HOME=/hf -e MPLBACKEND=Agg -e XC_TEST_PYTHON=/env/venv/bin/python)
fi

# Agent phase. The provider config is passed on stdin (never printed) and the
# OpenCollab configs/ folder is masked. Hidden tests and references are absent.
# Only this run's own output folder is mounted: in t3_lruttl duo r0 a coder ran
# `find /` and saw other runs' exported workspaces under /out.
# Framework under test: the pristine clone vendor/OpenCollab-upstream (pinned to
# 78ca8e3, never edited). Only "+guard" runs use vendor/OpenCollab, the working
# copy that carries the proposed change. The venv is an editable install that
# imports whatever is mounted at /kaohe/vendor/OpenCollab.
FRAMEWORK="$K/vendor/OpenCollab-upstream"
if [ "${GUARD:-0}" = "1" ]; then FRAMEWORK="$K/vendor/OpenCollab"; fi
SKILL_ARGS=()
if [ "${SKILLS:-0}" = "1" ]; then
  FRAMEWORK="$K/vendor/OpenCollab-skills"
  SKILL_ARGS=(-v "$(cygpath -m "$SKILLS_LIB"):/skills:ro" -e OPENCOLLAB_SKILLS_DIR=/skills
              -e XC_SKILLS_LIB="${SKILLS_TAG:-$(basename "$SKILLS_LIB")}")
fi
# "<method>+shared": Team with seat_budget="shared" on vendor/OpenCollab-fix-budget
# (branch feat/team-seat-budget). The default equal split needs no flag.
case "$METHOD" in *+shared)
  FRAMEWORK="$K/vendor/OpenCollab-fix-budget"
  SKILL_ARGS+=(-e XC_SEAT_BUDGET=shared) ;;
esac
# "<method>+mem-<insights|examples|both>": two-layer experience memory on
# vendor/OpenCollab-skills2; the frozen memory is MEMORY_LIB (default memory/lib2).
case "$METHOD" in *+mem-*)
  FRAMEWORK="$K/vendor/OpenCollab-skills2"
  MEMLIB="${MEMORY_LIB:-$P/memory/lib2}"
  SKILL_ARGS+=(-v "$MEMLIB:/memory:ro" -e XC_MEMORY=/memory -e XC_MEMORY_LAYERS="${METHOD##*+mem-}") ;;
esac
# "<method>+tmem-<insights|examples|both>": the same feature with the test memory
# memory/lib_tests (memory/build_test_memory.py), for the v7 Test Designer.
case "$METHOD" in *+tmem-*)
  FRAMEWORK="$K/vendor/OpenCollab-skills2"
  MEMLIB="${MEMORY_LIB:-$P/memory/lib_tests}"
  SKILL_ARGS+=(-v "$MEMLIB:/memory:ro" -e XC_MEMORY=/memory -e XC_MEMORY_LAYERS="${METHOD##*+tmem-}") ;;
esac
FRAMEWORK_REV=$(git -C "/${FRAMEWORK/:/}" rev-parse --short HEAD)
FRAMEWORK_DIRTY=$(git -C "/${FRAMEWORK/:/}" status --porcelain --untracked-files=no | wc -l)
# Per-container memory cap: an agent once ran a brute-force search that took the
# whole Docker VM (7.6 GB) and another run failed with ENOMEM. The cap confines
# such a runaway to its own run.
MEM="${MEM:-1800m}"
MSYS_NO_PATHCONV=1 docker run --rm -i --memory "$MEM" --memory-swap "$MEM" \
  -v "$FRAMEWORK:/kaohe/vendor/OpenCollab:ro" \
  --tmpfs /kaohe/vendor/OpenCollab/configs \
  -v "$FRAMEWORK/configs/team.collab.yaml:/teamcfg/team.collab.yaml:ro" \
  -e XC_FRAMEWORK="${FRAMEWORK##*/}@${FRAMEWORK_REV}+dirty${FRAMEWORK_DIRTY}" \
  -v "$P/workflows:/kaohe/oc-crosscheck/workflows:ro" \
  -v "$P/xc:/kaohe/oc-crosscheck/xc:ro" \
  -v "$P/scripts:/kaohe/oc-crosscheck/scripts:ro" \
  -v "$P/$TASKROOT/$TASK/task.md:/task/task.md:ro" \
  -v "$P/$TASKROOT/$TASK/repo:/task/repo:ro" \
  -v "$P/results/raw/$RUN_ID:/out/$RUN_ID" \
  -v oc-venv:/venv:ro \
  "${EXTRA[@]}" "${SKILL_ARGS[@]}" \
  -e OPENCOLLAB_WORKFLOWS_DIR=/kaohe/oc-crosscheck/workflows \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e OPENCOLLAB_MAX_OUTPUT_TOKENS="${MAX_OUT:-32768}" \
  -e OPENCOLLAB_CANDIDATE_PATH_GUARD="${GUARD:-0}" \
  -w /tmp \
  oc-crosscheck:dev \
  /venv/bin/python /kaohe/oc-crosscheck/scripts/run_agent.py \
    --task-dir /task --method "$METHOD" --run-id "$RUN_ID" --out /out --budget "$BUDGET" \
  < "$ENV_FILE"

# Grading phase (no model access needed; repository tasks without network).
MSYS_NO_PATHCONV=1 docker run --rm --memory "$MEM" --memory-swap "$MEM" \
  -v "$P:/kaohe/oc-crosscheck" -v oc-venv:/venv:ro -e PYTHONDONTWRITEBYTECODE=1 \
  "${GRADE_EXTRA[@]}" \
  -w /kaohe/oc-crosscheck oc-crosscheck:dev \
  /venv/bin/python scripts/finish_run.py --task "$TASK" --method "$METHOD" --rep "$REP" --run-id "$RUN_ID"
