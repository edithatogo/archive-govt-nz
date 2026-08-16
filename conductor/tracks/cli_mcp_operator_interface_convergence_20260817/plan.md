# Track 8 Plan: CLI/MCP and Operator-Interface Convergence

## Phases

### Phase 1: Canonical Command Hierarchy
- [ ] Build `src/archive_govt_nz/cli/main.py` using `argparse` with rich structured output.
- [ ] Implement `doctor`, `version`, `capabilities`, and `sources` subcommands.

### Phase 2: Compatibility Shims & Packaging
- [ ] Implement `src/archive_govt_nz/cli/compat.py` translating legacy arguments.
- [ ] Configure `[project.scripts]` in `pyproject.toml`.

### Phase 3: Contract Testing & Error Handling
- [ ] Add snapshot tests for CLI JSON outputs and exit codes.
- [ ] Run full 18-stage assurance check.
