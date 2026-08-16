# Track 8 Specification: CLI/MCP and Operator-Interface Convergence

## Purpose
Unify the command-line interface under `archive-govt-nz`, providing full backwards-compatible CLI entry point shims for legacy `sm-govt-nz` and `nz-govt-social` invocations.

## Context & Objectives
1. Implement canonical `archive-govt-nz` command hierarchy with `--json` support across all operations.
2. Provide wrapper shims `sm-govt-nz` and `nz-govt-social` mapping legacy arguments to canonical commands with helpful migration notices.
3. Standardize POSIX exit codes (0 through 5) and structured error envelopes.
4. Document the deferral rationale for an MCP server surface until explicit downstream consumer demand arises.

## Deliverables
- `src/archive_govt_nz/cli/main.py`
- `src/archive_govt_nz/cli/compat.py`
- CLI test fixtures and command contract tests
