# Requirements

## Must

- Inventory legislation consolidation receipts, reports, evaluators, reviews, closeouts, and public completion claims.
- Add a canonical typed index classifying each artefact as active, superseded, invalidated, historical, incomplete, or externally blocked.
- Preserve historical artefacts byte-for-byte and correct claims through additive superseding records and explicit links.
- Separate code/capability migration, operational-state migration, corpus custody/recoverability, and publication-identity migration.
- Use the canonical coverage evidence for the 68 candidate batches and never treat 33,693 candidates as acquired or content-verified records.
- Reject active evaluator inputs that rely on invalidated evidence.
- Produce `evidence-index.json` and `corrected-closeout.md` with exact evidence and run identities.

## Should

- Make classification and evaluator validation deterministic, fail closed, and independently testable.

## Excluded

- Prompt 18 GitHub release-note correction, Prompt 15 public Hub metadata, Prompt 19 donor presentation, external publication, historical evidence rewrites, and changes to `edithatogo/legislation`.
