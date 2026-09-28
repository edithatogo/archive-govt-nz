# Context Gold readable quality report — 2026-09-29

## Delivered

Contextual Gold now writes `context-quality-report.md` alongside its three
Parquet products. It is generated from the same verified per-series status and
coverage rows, reports exact source identity/vintage and eligible/excluded
counts, and states that observed period tokens are not a complete calendar.
The report retains explicit boundaries for continuity, joins, denominators,
rights, and publication.

The Markdown bytes are included in product hashes and the exact package
inventory. The contextual Gold verifier now requires all four products and
checks their byte fixity; CLI/MCP verification uses the updated closed result
schema.

## Validation

- Focused Context Gold builder/verifier tests: 30 passed.
- Ruff and basedpyright: passed.
- `./scripts/validate.sh`: passed locally; 7,093 passed, 9 skipped, 98.18%
  branch coverage; 52 schemas/42 representative documents; parity 9/9; all
  mutation, benchmark, vulnerability, licence, secret, and SBOM checks passed.
  Hosted exact-head checks are pending.

## Limits

This is a descriptive local report for four pinned contextual series. It does
not infer chronology or missing periods and does not establish rights,
analytical suitability, denominator approval, or publication.
