# Plan: CLI Contract and nzlc Compatibility

1. **Phase 1: CLI Wiring to LegislationArchiveService**
   - Connect `legislation` CLI action to `LegislationArchiveService` dynamic coverage report.
   - Eliminate hardcoded percentage constants.
2. **Phase 2: Legacy Entrypoints and Deprecation Warnings**
   - Preserve `nzlc`, `sm-govt-nz`, and `nz-govt-social` compatibility wrappers in `src/archive_govt_nz/cli_compat.py`.
3. **Phase 3: CLI & Compatibility Testing**
   - Verify all CLI commands in both `text` and `json` formats under `tests/cli/test_cli.py`.
   - Verify non-breaking deprecation notices.
