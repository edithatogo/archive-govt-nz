# Interface & CLI Reconciliation Map

## 1. CLI Commands and Compatibility Shims

To maintain complete backward compatibility for automated scripts and external operators, the following entry points will be supported:

| Command | Status | Canonical Implementation | Notes |
| :--- | :--- | :--- | :--- |
| `archive-govt-nz` | **Canonical** | `src/archive_govt_nz/cli.py:main` | Primary command surface for all archival, discovery, and publication operations. |
| `sm-govt-nz` | **Compatibility Shim** | `src/archive_govt_nz/cli/compat.py:sm_govt_nz_main` | Delegates to `archive-govt-nz capture --family social` with deprecation warning. |
| `nz-govt-social` | **Compatibility Shim** | `src/archive_govt_nz/cli/compat.py:nz_govt_social_main` | Alias for `sm-govt-nz` legacy invocations. |

## 2. Canonical Subcommand Grammar

All commands follow a structured verb-noun hierarchy and emit machine-readable JSON when `--json` is supplied:

```bash
# System introspection
archive-govt-nz version [--json]
archive-govt-nz doctor [--json]
archive-govt-nz capabilities [--json]

# Source discovery and registry
archive-govt-nz sources list [--agency <slug>] [--family <type>] [--json]
archive-govt-nz sources validate [--source-id <id>] [--json]

# Capture execution
archive-govt-nz capture plan --source-family <all|ckan|social|feeds|web|newsletters> [--out plan.json]
archive-govt-nz capture run --plan <plan.json> [--concurrency <int>] [--objects-dir <dir>]
archive-govt-nz capture status [--run-id <id>]

# Preservation & Integrity
archive-govt-nz archive verify --manifest <manifest.json> [--check-cas]
archive-govt-nz archive triangulate --url <url> [--service wayback|commoncrawl]
archive-govt-nz archive compact --input-dir <dir> --output-dir <dir>

# Derivatives & Search
archive-govt-nz derivatives build --objects-dir <dir> --output-dir <dir>
archive-govt-nz search query "<search_term>" [--format <format>] [--limit <int>]

# Publication & Distribution
archive-govt-nz publish plan --target <huggingface|zenodo|osf|all> [--version <YYYY-MM>]
archive-govt-nz publish run --plan <pub_plan.json> [--dry-run]
archive-govt-nz publish verify --target <target> --deposition-id <id>
```

## 3. Exit Code Contract

`archive-govt-nz` adheres to deterministic POSIX exit codes:

| Code | Label | Meaning |
| :--- | :--- | :--- |
| `0` | `SUCCESS` | Operation completed successfully and evidence was recorded. |
| `1` | `GENERAL_ERROR` | Unhandled internal exception. |
| `2` | `CONFIGURATION_ERROR` | Invalid CLI arguments or malformed configuration schema. |
| `3` | `POLICY_BLOCKED` | Request blocked by rights, embargo, license restriction, or WAF. |
| `4` | `NETWORK_FAILURE` | Upstream network timeout or transient HTTP failure after retry budget. |
| `5` | `INTEGRITY_VIOLATION` | SHA-256 fixity check failed, CAS mismatch, or manifest corruption. |

## 4. MCP (Model Context Protocol) Surface Evaluation

- **Status**: `DEFERRED` (Track 8).
- **Evaluation**: Neither `sm-govt-nz` nor `archive-govt-nz` currently has external consumers requesting an active MCP server surface. Standard JSON-emitting CLI commands provide full programmatic access for local AI agents and background workers. An MCP adapter will be designed if an explicit agent consumer arises.
