# Track: New Zealand Health Appropriations Medallion Assimilation

## Overview

This approved, in-progress track implements zero-loss assimilation of the pinned
`nz_health_appropriations` donor into Archive Govt NZ. It extends the corpus
with directly relevant official fiscal/health series and defensible contextual
denominators, using a strict Bronze → Silver → Gold → Platinum contract.

The design retains all donor files and acquired originals as immutable Bronze
objects outside Git. It assigns typed records and lineage to Silver, rebuildable
analytics to Gold, and rights-aware metadata and publication to Platinum.
Completed preservation and publication receipts do not establish completion of
every planned record set, measure or operational workflow.

## Artifacts

- [Hash-bound embedded-notice observations](./embedded-notices.md)
- [Standalone Budget-package operations](./budget-operations.md)
- [Specification](./spec.md)
- [Requirements](./requirements.md)
- [Design](./design.md)
- [Implementation plan](./plan.md)
- [Autonomous continuation route](./continuation.md)
- [Portable candidate original paths](./candidate-paths.md)
- [Pinned donor behavior](./donor-behavior.md)
- [Raw Budget extraction](./raw-budget.md)
- [Budget successor pilot and versioned contracts](./raw-budget-successors.md)
- [Raw BEFU/HYEFU extraction](./raw-forecast.md)
- [BEFU 2026 / HYEFU 2025 versioned source pilots](./forecast-successors.md)
- [Exact-series CPI source extraction](./cpi-source.md)
- [Raw historical Health/GDP extraction and reconciliation](./raw-historical.md)
- [Original-workbook orchestration](./raw-rebuild.md)
- [Typed workbook inspection](./workbook-inspection.md)
- [Raw compatibility projection and export contract](./raw-compatibility.md)
- [Source-derived analytical contracts](./raw-analytics.md)
- [Verified source-derived Gold export](./raw-gold.md)
- [Source-derived plot contracts and visual QA](./raw-plots.md)
- [Next raw-source ranges and semantic boundaries](./next-source-ranges.md)
- [Metadata](./metadata.json)
- [Run log](./runlog.md)
- [Evidence](./evidence.md)
- [Machine evidence](./evidence.jsonl)
- [Cutoff-bound source census](./source-census.json)
- [Self-review](./review.md)

## Current state

- Track state: `in_progress`.
- Scope and plan: explicitly approved on 2026-08-29.
- Donor preservation: 23/23 paths imported into external Bronze CAS and
  reconstructed, according to the recorded preservation receipts.
- Official source census: 73 captured resources and 68 discovery-only entries
  in the recorded 141-entry census; discovery is not capture.
- Exact CPIQ.SE9A source adapter: PR #271 observed merged after seven passing
  exact-head checks (1,956 hosted tests). Independent local builds retain 449
  selected facts, including 27 literal NA values, 4,041 lineage entries and
  all 22,701 source-row dispositions. Base metadata and real/per-capita products
  remain unresolved; the two local full-harness timeouts remain recorded.
- Derivatives: 312 Silver records, 1,699 field-lineage records and 12 Gold
  artifacts; donor SQLite parity and clean-room rebuild receipts are recorded.
- Separate raw Budget extraction: 215 Health facts, 3,655 cell-lineage rows
  and 6,504 input dispositions; all seven donor appropriation fields match in
  order. These new local outputs do not replace the published derivatives.
- Budget 2026 successor: 185 facts, 3,145 lineage entries and all 6,451 row
  dispositions in a separate pinned package, with independent XML reconciliation
  and two byte-identical builds. Standalone reader PR #273 is merged after seven
  exact-head checks; 61 focused tests achieve 100% critical coverage and the
  recovered cold mutation run kills all 110 mutants. The interrupted worktree
  loss and local timeout remain recorded separately.
- Separate raw BEFU/HYEFU extraction: 20 Health facts, 120 field-lineage rows
  and 4,665 cell dispositions; both ten-row donor summaries match in order.
  Actual/Forecast and vintage are retained; fiscal-year basis remains flagged.
- Separate raw historical extraction: 106 Health/GDP facts, 1,143 lineage rows,
  1,503 cell dispositions, 29 source-only annotated years and one explicitly
  retained precision difference. Historical extraction delivered in PR #232.
- Manifest-driven raw rebuilding: four stages, 341 selected facts, 18 files,
  independent byte-identical rebuild and verified complete-run reuse. This
  local operational result does not replace the published donor-derived data.
- Read-only raw-run CLI/MCP verification: matching live receipts, exact
  manifest pins, source/derivative fixity checks and no creation on missing state.
- Typed workbook inspection delivered in PR #245, with bounded decoded previews
  and original-byte verification. No formula evaluation or fact promotion.
- Persistent raw compatibility export locally validates all 341 facts, retains
  4,918 lineage rows and flags 15 binary representation differences. Independent
  builds match; all 312 donor SQLite rows are retained plus 29 historical years.
  Source-derived Gold tables and CLI now rebuild locally with all 321 selected
  analytical facts and 4,798 lineage records. PR #261 merged after seven
  exact-head checks passed; local timing failures remain recorded. Six new
  source-derived PNGs have matching independent builds and completed visual
  QA; final local assurance passes 1,906 tests and 128 current critical mutants.
  Plot PR #269 merged after all seven exact-head checks passed. Donor failure
  conformance and the four-profile pipeline pass 253 focused and 1,907 full
  tests. PR #270 is merged with seven successful exact-head checks and identical
  head/merge trees; this remains separate from broader source-area coverage.
- Hugging Face: `published_and_verified` for the pinned candidate, with
  [dataset](https://huggingface.co/datasets/edithatogo/nz-health-appropriations)
  revision `9b85bac06597d4435fd078f6bed0f30bb008542b` and manifest SHA-256
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
  The existing receipt records 94 remotely verified manifest entries.
  Public revision visibility and HEOR collection membership were re-observed
  on 2026-08-30; the full byte audit was not repeated during that check.
- Parent issue: [#205](https://github.com/edithatogo/archive-govt-nz/issues/205).
  Issue closure is not evidence of full implementation; the plan and receipts
  remain the acceptance-criteria authority.

Full assimilation is not complete. Remaining plan work includes format-support
contracts, contextual-series semantics,
expanded normalization/analytics and operational/recovery coverage. Consult
[the plan](./plan.md) for individual pending tasks; do not infer their completion
from publication or green CI.

Donor retirement remains outside this track (W-02). The donor was observed
unarchived on 2026-08-30. Originals and the existing published candidate are not
rewritten by subsequent inventory improvements. Historical observations in
`metadata.json` and the append-only evidence ledger retain their original dates;
they are not current-state assertions.

- [Implementation Plan](plan.md)
