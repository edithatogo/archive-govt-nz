# Interface & CLI Reconciliation Map

## 1. CLI commands and compatibility shims

These are the installed entry points. Compatibility means forwarding the
supplied arguments with a deprecation warning; it does not establish behavioural
parity with every historical donor release.

| Command | Status | Canonical Implementation | Notes |
| :--- | :--- | :--- | :--- |
| `archive-govt-nz` | **Canonical** | `archive_govt_nz.cli:main` | Current typed command surface. |
| `sm-govt-nz` | **Compatibility shim** | `archive_govt_nz.cli_compat:compat_sm_govt_nz_main` | Emits a deprecation warning, then forwards arguments to the canonical CLI. |
| `nz-govt-social` | **Compatibility shim** | `archive_govt_nz.cli_compat:compat_nz_govt_social_main` | Emits a deprecation warning, then forwards arguments to the canonical CLI. |
| `nzlc` | **Legislation compatibility shim** | `archive_govt_nz.cli_compat:compat_nzlc_main` | Maps the bounded legacy action names implemented in `cli_compat.py`; legislation hardening remains a later track. |

## 2. Implemented global grammar

Global commands are single Cyclopts commands. Structured output uses
`--format json`; there is no global `--json` alias and no nested `plan`, `run`,
`query`, `verify`, or `compact` verb beneath these commands.

```bash
# System introspection
archive-govt-nz version [--format text|json]
archive-govt-nz doctor [--format text|json]
archive-govt-nz capabilities [--format text|json]

# Source discovery and registry
archive-govt-nz sources [--registry-path <dir>] [--format text|json]

# Capture execution
archive-govt-nz capture [--uri <uri>] [--source-type <type>] [--format text|json]
# Global source types currently fail closed as not_configured (exit 2).

# Preservation & Integrity
archive-govt-nz archive --action count|verify [--output-dir <dir>] \
  [--manifest-path <manifest.json>] [--format text|json]
archive-govt-nz replay [--cas-dir <dir>] [--format text|json]
archive-govt-nz verify [--cas-dir <dir>] [--schemas-dir <dir>] \
  [--provenance-path <file>] [--format text|json]
archive-govt-nz provenance [--ledger-path <file>] [--format text|json]

# Derivatives & Search
archive-govt-nz derivatives [--output-dir <dir>] [--format text|json]
archive-govt-nz search <query> [--index-dir <dir-or-manifest>] \
  [--format text|json]

# Publication & Distribution
archive-govt-nz publish --target dry-run|huggingface|hf|zenodo \
  --staging-dir <dir> [--repository <owner/name>] [--format text|json]
# This validates and prepares a package locally; it does not publish remotely.
```

## 3. Exit Code Contract

`archive-govt-nz` adheres to deterministic POSIX exit codes:

| Code | Label | Meaning |
| :--- | :--- | :--- |
| `0` | `BOUNDED_SUCCESS` | The requested bounded observation, verification, or local preparation succeeded. |
| `1` | `NO_STATE_OR_FAILED_VERIFICATION` | Required local state is missing, corrupt, or failed integrity/runtime validation. |
| `2` | `NOT_CONFIGURED_OR_REDIRECT` | The requested route is unavailable or must use a domain command. |
| `3` | `POLICY_BLOCKED` | Explicit rights state does not allow redistribution. |
| `4` | `RETRYABLE_NETWORK_FAILURE` | Reserved for a bounded network failure; the corrected global local commands do not currently emit it. |
| `5` | `UNSUPPORTED_REQUEST` | The requested target or action is unsupported. |

An exit code is bounded to the invoked command. Code 0 never proves corpus
completeness, remote publication, rights clearance beyond the supplied package,
recovery, or cutover.

## 4. MCP (Model Context Protocol) Surface Evaluation

- **Status**: A legacy MCP entry point exists, but current-standard and
  current-`main` hardening remains pending in the ordered MCP track.
- **Boundary**: CLI validation does not establish MCP protocol conformance or
  operational readiness. The MCP track must be reviewed independently after the
  service, global CLI, and legislation CLI sequence.
