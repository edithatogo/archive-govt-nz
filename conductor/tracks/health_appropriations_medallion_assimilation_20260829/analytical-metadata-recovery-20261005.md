# Analytical products and metadata recovery — 2026-10-05

The recovery command extends the existing Fiscal lane to reconstruct Budget
comparison and the two local metadata packages from original bytes. It consumes
no retained Silver, Gold or metadata products. Native installed-command replay and final repository validation pass. This
closes only the supported analytical products and metadata recovery scope.

`health-appropriations-recover-analytical-metadata ARCHIVE OUTPUT` verifies the
source pins and output separation without writing. `--write` reserves a new
output directory and keeps two independent builds under `first` and `second`.
Existing outputs are rejected and partial failures remain available for diagnosis.

The exact source set contains the reviewed historical Fiscal workbook, CPI and
annual population objects, Budget 2025 and 2026 workbooks, and the three separately
pinned period/definition observations. Budget capture locator/timestamp values
reproduce the retained manifests; they are not new captures. Definitions and all
five original objects are hash-checked before output creation and after builds.

Each run creates supported Fiscal Silver/canonical products, Fiscal analytical
Gold, 6 report plots and report metadata, the two raw Budget packages,
Budget comparison Gold, the six-file local catalogue/DCAT/PROV package, and the
four-file discovery-candidate package. Existing Fiscal CLI/MCP/Arrow and report
readbacks remain part of the recovery lane. Both new metadata packages require
reconstruction verification. Full output inventories and product receipts must
agree across the two runs; disagreement does not produce a verified receipt.

Two focused tests cover changed-input preflight, actual installed CLI exit-2
behavior, exclusive output, repeat disagreement and source mutation during builds.
Controlled builder fixtures test orchestration guards only; native original-based
replay supplies product assurance. No extra tests are added for coverage inflation;
the repository coverage floor remains 80%.

The earlier external prototype replay produced 57 identical files per run, all
matching retained qualified Fiscal Gold/reports, Budget comparison and metadata
packages. The new installed command is separately replayed against a clean archive
containing only copies of the eight pinned input files. Its receipt must bind the
current production sources, recipe and lockfile before integration is recorded.

This scoped recovery does not cover every Health source family or all donor
SQLite/plot products. It does not approve source semantics, rights, federation,
public access, licensing or publication. Croissant/RO-Crate candidates remain
explicitly non-conforming and release-blocked until required metadata is evidenced.
The full Conductor Health completion review remains open.

The installed command exited 0, with two byte-identical 57-file inventories,
exact retained-product matches, eight copied inputs only, unchanged originals
and definitions, dry-run no-write, exclusive output exit 2 and changed-source
exit 2 before output creation. Required harness passed: 7,476 tests / 10 skips,
97.80% aggregate coverage with the 80% floor. The generic scoped phase review
passed; it is not the final whole-Health review. Native evidence is retained at
`ArchiveGovtNZ/health-appropriations/assurance/analytical-metadata-recovery-20261005-v2`.
