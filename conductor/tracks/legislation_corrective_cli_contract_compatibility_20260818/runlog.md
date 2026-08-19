# Run Log: CLI Contract and nzlc Compatibility

- Connected CLI `legislation` command directly to `LegislationArchiveService`.
- Eliminated static 100% constant and replaced with dynamic CAS coverage.
- Validated compatibility wrappers (`nzlc`, `sm-govt-nz`, `nz-govt-social`) with deprecation notices.
- Verified all 23 CLI test cases in `tests/cli/test_cli.py` pass cleanly.
