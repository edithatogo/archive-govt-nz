# Original-workbook archival rebuild

`archive-govt-nz health-appropriations-rebuild` replaces manual invocation of
the four current raw workbook adapters with one manifest-driven operation.
This is local Bronze-to-Silver orchestration, not publication or full-workbook
coverage. Historical, forecast and Budget facts retain their distinct schemas.

## Contract

- The default is read-only preflight. Supply a pinned donor-manifest SHA-256,
  the Bronze store root and an explicit timezone-aware observation timestamp.
  The command checks all four source paths and CAS objects before output.
- `--no-dry-run` opts into a new output directory. `PLAN.json` records source
  identities, profile vintages, manifest identity and observation context.
- Every stage retains the adapter's three Parquet files and manifest. The run
  manifest is written last and pins each stage manifest. Complete reuse checks
  the plan, all stage context, file sets and every output hash before succeeding.
- Output inside Bronze is prohibited. Symlinked run/stage/manifest/output
  targets are rejected. No existing artifact is overwritten.
- Failed stages leave their bytes and a redacted `FAILURE.json`. Partial or
  interrupted runs cannot be reused: choose a new directory. Partial-stage
  resume/scheduling remains a separate task, not an implied capability.
- A source with rejected rows or a partial receipt cannot produce a successful
  run. The CLI returns two on failure and reports only the exception class.
- The run does not concatenate unlike schemas, update donor-derived Gold,
  make rights decisions, modify HF files or retire the donor repository.

## Invocation

```sh
uv run --locked archive-govt-nz health-appropriations-rebuild \
  --donor-manifest "$HEALTH_ARCHIVE_ROOT/manifests/donor-4668e6c.json" \
  --store-root "$HEALTH_ARCHIVE_ROOT/bronze-cas" \
  --manifest-sha256 893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74 \
  --observed-at "$HEALTH_SOURCE_OBSERVED_AT" \
  --output-dir "$HEALTH_ARCHIVE_ROOT/silver/raw-run-new"
```

Review the preflight output, then use the same arguments with `--no-dry-run`
to build. Fixity verifies bytes, not authenticity or redistribution rights.
An observation timestamp is caller-supplied context, not a new HTTP capture.

## Live validation

`silver/raw-orchestrated-20260830-v1` in the external archive retains 18 files.
All match an independent rebuild byte for byte. Complete-run reuse reverified
the four CAS objects and every output. The selected record counts are 215
Budget, ten BEFU, ten HYEFU and 106 historical facts (341 total), with zero
rejected selected values. Source exclusions remain explicit in stage receipts.

Run manifest SHA-256:
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
Plan identity:
`f9414b07383568332a069f58b10d8e0f2e1ab57d2aa0db5d43ad2d3cd26ee07d`.
The observation context is `2026-08-30T08:58:00Z`, local source verification.
The source manifest is pinned in the invocation above; no original changed.

## Remaining integration

Read-only MCP reporting, partial-stage resumption, additional workbook areas,
source-to-oracle analytical reconstruction and new publication candidates are
separate acceptance work. Existing published dataset counts remain unchanged.
