# Run Log: Real Legislation CLI Service Integration and nzlc Compatibility

- Wired 11 real legislation subcommands in `src/archive_govt_nz/cli.py` to `LegislationArchiveService`.
- Created `src/archive_govt_nz/cli_compat.py` for legacy `nzlc` compatibility.
- Implemented 33 CLI tests in `tests/cli/test_cli.py` verifying dynamic coverage, missing states, and legacy invocation.
- Verified full 19-stage assurance gate (`tools/check.py`) with 590 tests passing and 95.49% coverage.
