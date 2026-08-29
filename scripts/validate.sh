#!/usr/bin/env bash
set -euo pipefail
uv run --locked python tools/check.py \
  --pytest-workers auto \
  --pytest-distribution loadscope
