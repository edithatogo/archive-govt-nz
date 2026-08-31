# Prompt 04 local canonical state merge

Current handoff: [execution 02](./current-package.json). The 552-record local package is verified. Final local validation and seven hosted checks passed at 1f0417f; the final documentation head must pass the same live gate before merge. Earlier pending-status paragraphs below are retained historical observations, superseded by the later verification sections.

Issue #292 under #276. Target baseline `6885c3e50e34f19f15459abe8eca1409675f068b`;
archived donor final head `b40587f1b1aec7356a0f623916fcc8212397d283`.
Target operational producer `97ae6067d7320fe634f5e202219c412cf4ba754a`, successful
run 33334725250 / artifact 9738685368, selected again immediately before execution.
No newer successful main-branch target harvest existed at that observation.

## Results

500 donor + 52 target records/work IDs/CAS objects = 552 each. All six identity
and hash overlap counts are zero. Zero conflicts, missing objects, duplicate
manifestation identities or orphan objects. `final-state-merge-receipt.json`
binds both raw manifests/checkpoints, artifact digests, descriptor hashes,
producer revisions, counts, semantic roots and the merger software commit.

`independent-readback-01.json` records 560 file readbacks, all 552 SHA-256/BLAKE3/
size checks, exact preservation of every parent record, checkpoint membership,
native manifest/checkpoint loader acceptance, a byte-identical reversed-order
package and idempotent canonical state. `package-inventory-01.json` binds every
package member. Parent archives retain their exact manifests, checkpoints,
source records, receipts, seed where present, and CAS bytes.

Neither parent declares a separate source_url or media_type field. Retrieved
manifestation URI, preferred canonical URI and dated expression identity are
checked; missing fields are explicitly reported rather than inferred. All 552
records retain null rights_statement and rights_review_required. This is not
redistribution clearance. Metadata conflicts, including rights differences, block
without choosing a winner. Legitimate dates/formats remain distinct and linked
in versions_by_work.json. Identical bytes deduplicate, including across versions.

Conditional request caches are explicitly reset for unconditional revalidation;
original checkpoint caches remain preserved in the parent archives. The target
artifact does not contain an explicit prior-run restore receipt: cumulative
batch names are retained but earlier target artifact recovery is not claimed.

## Local package and invocation

The exclusive package is in the operator's external Quarantine under
`archive-govt-nz/canonical-state-merge-04/merged-01/`; independent reversed execution
is `reversed-01/`. Raw sources, extracted plain text, descriptors, parent ZIPs and
CAS remain there, outside Git. Files are read-only, not a WORM or redundant backup
claim. Rehash the completion inventory before consumption.

```sh
uv run --locked python tools/merge_legislation_states.py \
  --parent "$DONOR_ZIP" "$DONOR_DESCRIPTOR" \
  --parent "$TARGET_ZIP" "$TARGET_DESCRIPTOR" \
  --output "$NEW_EXCLUSIVE_EXTERNAL_DIRECTORY" \
  --software-commit "$REVIEWED_MERGER_COMMIT"
```

Descriptors are trusted inputs: independently obtain GitHub run/artifact metadata,
pin expected repository/run/artifact identities and digest, and bind the donor's
Prompt 03 eligible inventory. The tool has no network/latest-run selector. It
re-verifies both parents internally before merging. Existing output paths are
refused. Failed packages never receive COMPLETE.json; interruption/partial writes
must never be treated as canonical. A fresh directory is required for another run.

The native manifest root is the SHA-256 of sorted canonical record JSON using
existing producer serialization. The checkpoint is deterministically constructed
from union membership and completed batches. Whole-package lineage describes an
execution; algebraic idempotence applies to canonical records, objects and
checkpoint, not an ever-expanding history of repeated execution receipts.

## Validation and handoffs

Focused synthetic suite: 49 tests, 100% critical line and branch coverage.
Twelve targeted invariant mutants killed. Native schema acceptance is exercised
in tests. Full native and exact-head hosted checks are pending; no issue-complete
or merge claim yet. Development failures are retained in development-attempts.json.

- Prompts 06, 09 and 13: local canonical parent only; verify the full inventory
  before copying into a separately authorized execution. No workflow activated.
- Prompt 13: target prior-run restore lineage is absent from the supplied artifact;
  investigate without claiming earlier parent recovery from checkpoint names.
- Prompt 01: register #292 and this precise owned scope serially. Shared programme
  files and closeout reports are not changed by this implementation.

Only authenticated read-only GitHub metadata/artifact retrieval and authorized
issue/branch/PR traceability actions are in scope. No Hugging Face/Zenodo writes,
DOI minting, donor unarchive, schedule changes, secrets changes, source acquisition,
or independent edithatogo/legislation changes occurred.

## Superseding execution 02

The authoritative handoff is now `current-package.json` and
`execution-02/final-state-merge-receipt.json`, using software commit
`c4287a4eed4db5d5ae67746cc49287b37f4f914e` and external local `merged-02/`.
The root-level initial receipt and inventory remain historical and unchanged.
Canonical records, checkpoint and 552 objects are identical to execution 01;
execution receipts differ because they bind the corrected software.

Review found that the same archive passed twice with differing descriptors could
reference an unretained descriptor. `review-finding-01.json` retains reproduction
before modification. The added guard rejects that ambiguity; exact repetitions
remain idempotent. A regression test failed before the fix and passed afterward.
The final focused suite has 50 tests at 100% critical line and branch coverage.
Independent readback and reversed execution passed again for execution 02.
Full validation is being rerun after the review fix before issue completion.

## Final local validation

The full post-review harness passed: 2,644 tests, 97.00% overall coverage,
all repository schema/parity/mutation/workflow-policy lanes, dependency audit,
licence inventory, secret scan and strict SBOM validation (111 components).
`local-validation-final.json` binds the exact log and reviewed code. Hosted
checks and remote merge remain separate gates, not implied by these local passes.

## Rebased validation

After unrelated main advancement to 9e559799f441651e79d4109fcd28e5fa89be668e, the branch was rebased without changing merger, tests, schema or legislation parent dependencies. The complete native harness passed again: 2,761 tests, 97.05% overall coverage and all assurance/security/SBOM stages. See rebase-validation-final.json. The executed software revision remains remotely reachable; the execution-02 package and receipts remain unchanged.
