#!/usr/bin/env bash
set -euo pipefail

# Local feedback only. CI remains the authoritative full-suite gate.
exec uv run --locked pytest -m 'not slow' "$@"
