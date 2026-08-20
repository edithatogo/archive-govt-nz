# Run Log: CLI Contract and Non-Affirmative State Compatibility

- Refactored all non-legislation CLI commands in `src/archive_govt_nz/cli.py` to be truthful, evidence-driven, and non-affirmative:
  - `doctor`: evaluates real Python version (>= 3.11) and runtime health.
  - `capabilities`: reports static compiled engine capabilities with status `compiled` without claiming operational verification.
  - `sources`: inspects real seed registry paths, returning `not_configured` or `empty` with diagnostic on stderr when absent.
  - `capture`: rejects standalone invocation without active daemon, returning `not_configured` (exit code 2) and diagnostic on stderr.
  - `archive`: inspects real WARC/WACZ files and byte sizes; returns `no_state` (exit code 1) when directory is absent or empty.
  - `replay`: verifies actual CAS objects against their SHA-256 digests; returns `no_state` (exit code 1) when CAS is absent, and `failed` when corrupted.
  - `verify`: executes dynamic 5-point verification without hardcoded check numbers.
  - `provenance`: reads real evidence ledger at `evidence/archive-evidence-ledger.json` and counts actual tracked entities without hardcoded constants.
  - `derivatives`: reports compiled derivative types and observed file counts.
  - `search`: queries search index, returning `no_index` when directory is absent.
  - `publish`: inspects staging directory for dry-run and `HF_TOKEN` / `ZENODO_TOKEN` environment variables, returning `not_configured` (exit code 2) when absent.
- Preserved `legislation` command without wiring new subcommands.
- Updated `tests/cli/test_cli.py` with comprehensive positive and negative controls covering absent CAS, absent provenance ledger, absent publication tokens, non-existent sources, and valid execution paths in both text and JSON formats.
- Achieved 99.43% test coverage on `src/archive_govt_nz/cli.py`.
