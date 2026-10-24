#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$repo_root/.venv/bin/python"

if [[ ! -x "$python" ]]; then
  printf 'Missing repo-local Python 3.15.1: %s\n' "$python" >&2
  exit 2
fi

actual_version="$($python -c 'import platform; print(platform.python_version())')"
if [[ "$actual_version" != "3.15.1" ]]; then
  printf 'Expected repo-local Python 3.15.1, found %s\n' "$actual_version" >&2
  exit 2
fi

if [[ $# -eq 0 ]]; then
  printf 'Usage: %s <pytest path/node/options...> | --failed [pytest options...]\n' "$0" >&2
  printf 'Use --failed to run only cached failures; an empty cache verifies no tests.\n' >&2
  exit 2
fi

if [[ "$1" == "--failed" ]]; then
  shift
  exec "$python" -m pytest --lf --last-failed-no-failures=none "$@"
fi

exec "$python" -m pytest "$@"
