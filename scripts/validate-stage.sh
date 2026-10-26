#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  printf 'Usage: %s <stage> [stage ...]\n' "$0" >&2
  printf 'List stages with: uv run --locked python tools/check.py --list\n' >&2
  exit 2
fi

args=()
for stage in "$@"; do
  args+=(--stage "$stage")
done

exec uv run --locked python tools/check.py "${args[@]}"
