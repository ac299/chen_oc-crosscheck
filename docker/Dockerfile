# Linux runtime for OpenCollab experiments.
# OpenCollab needs fcntl/renameat2, so it cannot run on the Windows host.
# The OpenCollab checkout and this project are bind-mounted at run time;
# the Python environment lives in a Docker volume (/venv) created by `uv sync`.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates procps build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.9.* \
 && git config --system user.name "oc-experiment" \
 && git config --system user.email "oc-experiment@localhost" \
 && git config --system init.defaultBranch main \
 && git config --system --add safe.directory '*'

ENV UV_PROJECT_ENVIRONMENT=/venv \
    UV_CACHE_DIR=/uv-cache \
    UV_LINK_MODE=copy \
    PATH=/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /kaohe
