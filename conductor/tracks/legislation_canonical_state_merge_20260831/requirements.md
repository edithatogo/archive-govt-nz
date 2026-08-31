# Requirements

- MUST-1: Bind authenticated parent ZIP digests, repository revisions, roots, checkpoint membership, receipts and CAS.
- MUST-2: Exclusive outputs; deduplicate bytes, retain versions and parent lineage, ledger every conflict, fail closed on ambiguous identity.
- MUST-3: Deterministic and idempotent union with every record resolving to verified CAS.
- MUST-4: Recompute counts and supply local canonical parent for Prompts 06, 09 and 13 without publication.
- MUST-5: 100% critical line/branch coverage, property/negative/mutation checks and full native/exact-head hosted gates.
- SHOULD: Preserve complete parent packages for audit and reproducibility.
- WONT: Change schedules or remote publication.
