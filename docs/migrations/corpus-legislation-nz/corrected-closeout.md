# Corrected legislation consolidation closeout

This record supersedes the completion claims in
`docs/migrations/corpus-legislation-nz/consolidation-closeout-report.md` without
altering that historical file. It evaluates the consolidation at target commit
`6755e12a48536de938b6f5955fe974d4b1de1b75` and archived donor head
`b40587f1b1aec7356a0f623916fcc8212397d283`. A closed issue, merged pull
request, configured workflow, or green check is delivery evidence only; none is
treated as proof of acquisition, recovery, publication, or overall completion.

## Current status by independent dimension

| Dimension | Status | Current evidence and limit |
|---|---|---|
| Code/capability migration | **Complete** | The final donor lineage, capability matrix, target contracts and merged implementations account for the donor capabilities. Prompt 02 was delivered by issue #278 and PR #281 at merge `d6bc0c96`, with hosted runs `33391772554`, `33391772567`, and `33391772652`. This status concerns code and contracts only. |
| Operational-state migration | **Incomplete** | The deterministic canonical-state merge passed, but the target-owned 500-work proof is a blocked, non-dispatched observation. Its receipt records seven blockers and leaves every acquisition, fixity, reconciliation, continuation, and durable-recovery proof false. Prompt 13 issue #335 remains open; merged PR #336 at `a9262803` preserves the blocked receipt rather than proving operation. |
| Corpus custody/recoverability | **Externally blocked** | Prompt 09 produced a deterministic local package, but its evidence records rights blocking, no remote payload authority, no publication readback, and no Prompt 10 recovery acceptance. Prompt 10 issue #327 and draft PR #329 remain preparation only. A local package is not durable remote custody or independent recovery proof. |
| Publication-identity migration | **Externally blocked** | The Zenodo concept/version relationship was corrected and verified read-only by Prompt 16, issue #343 and PR #344 at merge `6755e12a`; hosted runs were `33520524492`, `33520524545`, `33520524568`, and `33520524599`. No Zenodo record was changed or version minted. The Hugging Face candidate manifest remains `candidate_only_not_published`; external publication approval is pending under issue #341 even though PR #342 merged at `0158b462`. |

The programme therefore has no single truthful “consolidation complete” state.
Only the code/capability dimension is complete. The remaining dimensions retain
their independent incomplete or externally blocked status.

## Coverage correction

The canonical Prompt 14 coverage report establishes four distinct populations:

- 33,693 unique, search-derived **candidate identifiers** in 68 exact batch
  files, with concatenated SHA-256
  `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`;
- 500 identifiers in the governed reviewed seed;
- 552 works and 552 records in canonical target state; and
- 552 verified CAS objects in that state.

Attempted, successfully retrieved, expression, manifestation, normalised,
published, failed, unavailable, deferred, rights-blocked, and not-attempted
counts remain unknown. Membership in the 33,693-candidate universe proves none
of those outcomes and does not prove complete legislative coverage. The other
33,193 candidates outside the reviewed seed have no inferred disposition.

The stale “67 historical batches” blocker is superseded only as a candidate
inventory accounting issue: Prompt 14 verifies 68 exact batch files and their
33,693 unique candidate identifiers. It does not establish that those
identifiers were acquired, content-verified, stored, or published. Earlier
parity receipts that report 33,693 reconciled records or 100% corpus parity are
invalidated and cannot resolve an operational or publication claim.

## Preserved historical record

The following artefacts remain unchanged for auditability and are classified in
the canonical evidence index:

- the original closeout and parity reports;
- the invalidated consolidation, cutover, observation, and state-transfer
  receipts;
- `dec-hist-001-finding.md` and its unsupported CAS/publication conclusions;
- the 2026-08-26 completion evaluator output that predates the canonical
  coverage and blocked operational proof;
- earlier failed verification and hosted-check attempts; and
- the complete imported donor snapshot under
  `conductor/archive/imported/corpus-legislation-nz/`.

Their historical wording is evidence of what was claimed at the time. The
active evaluator must use `evidence-index.json`, accept only evidence IDs listed
for the relevant dimension, and reject invalidated evidence as proof.

## Current gates and handoff

Prompt 06 issue #308 and Prompt 07 issue #310 remain open. Prompt 08 was merged
through issue #312 and PR #317 at `efca467e`; Prompt 09 through issue #321 and
PR #324 at `d3946b8f`; and Prompt 12 through issue #333 and PR #334 at
`2c15dcc3`. Those merges do not override the later Prompt 13 blocker receipt.

No external dataset, metadata, DOI, release, or archived donor record was
modified for this correction. Completion can advance only through new,
independently verified evidence for the affected dimension. Historical bytes
must not be rewritten to make a later gate appear satisfied.
