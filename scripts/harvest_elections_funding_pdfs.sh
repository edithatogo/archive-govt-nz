#!/usr/bin/env bash
# Harvest remaining elections.nz candidate/candidate-expense PDFs via Chrome CDP.
# Requires a headed Chrome started with --remote-debugging-port=9222.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUEUE="${1:?usage: harvest_elections_funding_pdfs.sh <url-list-file> [workers]}"
WORKERS="${2:-3}"
OBJECTS_DIR="$REPO_ROOT/objects"
DONE_FILE="$REPO_ROOT/.harvest-done.txt"

mkdir -p "$OBJECTS_DIR"
touch "$DONE_FILE"

if ! curl -sf http://localhost:9222/json/version >/dev/null; then
  echo "Chrome CDP endpoint on :9222 is not available." >&2
  echo "Start it with:" >&2
  echo "  \"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" \\" >&2
  echo "    --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-cdp-profile \\" >&2
  echo "    --no-first-run --no-default-browser-check \\" >&2
  echo "    --disable-blink-features=AutomationControlled about:blank" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT/.harvest-logs"
for ((i = 0; i < WORKERS; i++)); do
  node "$REPO_ROOT/tools/cdp_harvest_worker.mjs" \
    "$QUEUE" "$OBJECTS_DIR" "$i" "$WORKERS" "$DONE_FILE" \
    >"$REPO_ROOT/.harvest-logs/worker-$i.log" 2>&1 &
done
wait
echo "Harvest complete. Objects in $OBJECTS_DIR"
