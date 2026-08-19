# Requirements: CLI Contract and nzlc Compatibility

Track: `legislation_corrective_cli_contract_compatibility_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#135](https://github.com/edithatogo/archive-govt-nz/issues/135)

## MoSCoW Requirements

### Must
1. **Contractual CLI Commands**:
   - Support `doctor`, `capabilities`, `sources`, `capture`, `archive`, `replay`, `verify`, `provenance`, `derivatives`, `search`, `publish`, and `legislation` commands in `src/archive_govt_nz/cli.py`.
   - Support both `text` and structured `json` format outputs.
2. **Standardized Process Exit States**:
   - Enforce process exit codes from `src/archive_govt_nz/exit_codes.py` (0 for SUCCESS, 10 for UNCHANGED, 20 for PARTIAL_SUCCESS, 30 for RESTRICTED, 40 for RETRYABLE_FAILURE, 50 for TERMINAL_FAILURE).
3. **Application Service Integration**:
   - Wire `legislation` command directly to `LegislationArchiveService` without hardcoded constants or simulated affirmative strings.
4. **Donor Entrypoint Compatibility (`nzlc`)**:
   - Provide non-breaking wrapper entrypoints in `src/archive_govt_nz/cli_compat.py` for legacy commands (`nzlc`, `sm-govt-nz`, `nz-govt-social`) emitting stderr deprecation warnings.
