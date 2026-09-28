# Context Gold source-quality report — 2026-09-28

## Delivered

The four pinned CPI, QES wage, GDP and annual population contextual Silver
series now include a deterministic `context_quality.parquet` product. It reports
per exact source-series identity the observation, eligible and excluded counts,
reason-coded exclusions from retained Silver facts, and the distinct observed
period tokens. It does not infer missing periods because source calendars have
not been supplied and the series must remain separate.

The report carries explicit `period_continuity: not_assessed_source_calendar_not_supplied`,
`rights_state: not_evaluated`, and `denominator_selection: not_performed` states.
The source marker pins remain part of the build receipt and all three output
Parquet files participate in deterministic hashes and readback checks. The CLI
and MCP preflight receipt exposes a compact source-quality status summary; MCP's
closed output schema was updated accordingly.

## Validation

- Focused Context Gold suite: 12 passed.
- Ruff and basedpyright: passed.
- `./scripts/validate.sh`: passed; 7,084 tests, 9 skipped; formatting, lint,
  typing, schema checks, mutation suites, benchmark, dependency audit, licence
  inventory, secret scan and SBOM gates passed. Local only; hosted exact-head
  assurance remains separate.

## Limits

This is quality reporting for four explicitly pinned local context packages,
not a whole-census source-health or future-vintage report. Rights, source
calendar completeness, denominator selection, cross-source joins, real-value
conversion and publication remain unassessed or unperformed.
