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

- [Specification](./spec.md)
- [Requirements](./requirements.md)
- [Design](./design.md)
- [Implementation plan](./plan.md)
- [Autonomous continuation route](./continuation.md)
- [Pinned donor behavior](./donor-behavior.md)
- [Raw Budget extraction](./raw-budget.md)
- [Raw BEFU/HYEFU extraction](./raw-forecast.md)
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
- Derivatives: 312 Silver records, 1,699 field-lineage records and 12 Gold
  artifacts; donor SQLite parity and clean-room rebuild receipts are recorded.
- Separate raw Budget extraction: 215 Health facts, 3,655 cell-lineage rows
  and 6,504 input dispositions; all seven donor appropriation fields match in
  order. These new local outputs do not replace the published derivatives.
- Separate raw BEFU/HYEFU extraction: 20 Health facts, 120 field-lineage rows
  and 4,665 cell dispositions; both ten-row donor summaries match in order.
  Actual/Forecast and vintage are retained; fiscal-year basis remains flagged.
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
contracts, donor failure-behavior characterization, contextual-series semantics,
expanded normalization/analytics and operational/recovery coverage. Consult
[the plan](./plan.md) for individual pending tasks; do not infer their completion
from publication or green CI.

Donor retirement remains outside this track (W-02). The donor was observed
unarchived on 2026-08-30. Originals and the existing published candidate are not
rewritten by subsequent inventory improvements. Historical observations in
`metadata.json` and the append-only evidence ledger retain their original dates;
they are not current-state assertions.

- [Implementation Plan](plan.md)
