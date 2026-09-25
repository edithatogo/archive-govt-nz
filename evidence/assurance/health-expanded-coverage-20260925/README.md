# BEFU core-expense source-selection checkpoint

This additive checkpoint records one explicit selection for the retained
BEFU 2026 core Crown expense Silver package. The prior 12-selection report and
its evidence remain unchanged; this one-row report is not a complete source
census and does not replace the prior report.

The selection binds source SHA-256
`313ee040abd9a332cc36245da5a0c2cb0d38fe2cedc013d731c1f12db463b0d1`, source
locator, `BEFU-2026` vintage and Silver manifest SHA-256
`23ddc3fb0a3d4d6dc55a4731694f7d9e26f5ace1324d4a76456f1ad761abe651`. The
report accepts only the profile's reviewed counts (10 normalized, 24 context,
2,341 preserved-only, zero rejected) and requires all three output hashes.

The report joins supplied metadata; it does not re-verify Parquet bytes,
requalify source rights, establish formula-cache freshness/currency/fiscal-year
semantics, qualify the whole source, or close the Health Appropriations phase.
The derivative remains context-only.

Replay from the repository root with the retained external archive:

```sh
uv run python evidence/assurance/health-expanded-coverage-20260925/replay.py \
  /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations
```

The retained `report.json` is a metadata-only replay output. Its presence does
not imply external acceptance or publication.

Replay output SHA-256: `60d369d085c1e7b7a7d15e9228eac3c14be5544864e9f31495a7b5cae6db2b7d`.
