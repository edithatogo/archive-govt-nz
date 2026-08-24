# Requirements: sm-govt-nz Donor Retirement Readiness

## Background
`evidence/migrations/sm-govt-nz/consolidation-closeout-receipt.json` records the
donor as archived with zero active workflows (closed 2026-08-18). GitHub state
as of 2026-08-24 contradicts this: `isArchived: false`, and scheduled workflows
ran today (Threads manual seed validation 04:07Z, HF rollover 05:52Z). The
capability migration is also incomplete: parity receipts exist for only five
source classes, and the canonical capture path is not yet activated.

## Core requirements
1. Issue a superseding corrected receipt; never rewrite the original.
2. No archival while donor workflows are the only healthy data collection path.
3. Parallel-operation verification: one full parity cycle per source class after
   multi-source capture activation completes.
4. Archival checklist executed in order: disable workflows -> soak window ->
   verify canonical-only operation -> final tag -> archive repository -> update
   registry and receipts.
5. Repository archival is an external, irreversible action: requires explicit
   maintainer authorization at the decision boundary.
