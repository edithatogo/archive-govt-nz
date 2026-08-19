# Plan: Truthful CLI Contract and Non-Affirmative State Compatibility

1. **Phase 1: Truthful Backend Wiring in `cli.py`**
   - Refactor `doctor` to perform real environment and Python checks.
   - Refactor `sources` to load from real seed paths or report `not_configured`.
   - Refactor `capture` to reject unconfigured daemon queues and report `unsupported` / `not_configured`.
   - Refactor `archive` to count or verify real WARC/CAS files, returning `no_state` if absent.
   - Refactor `replay` to execute real replay fixity or report `no_state`.
   - Refactor `verify` to execute dynamic multi-point validation or report real check results.
   - Refactor `provenance` to inspect `evidence/archive-evidence-ledger.json` and count real entities.
   - Refactor `publish` to inspect publication credentials/tokens and report `not_configured` when absent.
   - Refactor `search` to query real indexes or report `no_index`.
2. **Phase 2: Output and Exit Code Taxonomy**
   - Direct payload data to stdout and diagnostics to stderr.
   - Return documented exit codes within 0–5.
3. **Phase 3: Comprehensive Negative & Positive CLI Tests**
   - Implement tests covering absent CAS, absent provenance ledger, absent publication tokens, non-existent sources, and valid CLI runs.
4. **Phase 4: Full Verification Gate**
   - Run `uv run python tools/check.py` and ensure patch test coverage >= 95%.
