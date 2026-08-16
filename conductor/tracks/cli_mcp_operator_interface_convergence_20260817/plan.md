# Track 8 Plan: CLI/MCP and Operator-Interface Convergence

## Phases

### Phase 1: Canonical CLI Subcommands
- [x] Implement subcommands: `version`, `doctor`, `capabilities`, `sources`, `capture`, `archive`, `derivatives`, `search`, `publish`.
- [x] Standardize JSON envelopes with `--json` formatting.

### Phase 2: Donor Compatibility CLI Wrappers
- [x] Implement `compat_sm_govt_nz_main` and `compat_nz_govt_social_main` with stderr deprecation warnings.
- [x] Register legacy entry points in `pyproject.toml`.

### Phase 3: CLI Contract Testing & Quality Gates
- [x] Implement comprehensive CLI test suite in `tests/cli/test_cli.py`.
- [x] Run full 18-stage assurance check suite.
