# Independent durable legislation recovery

Prompt 10, issue [#327](https://github.com/edithatogo/archive-govt-nz/issues/327).
**INCOMPLETE: prerequisite audit only; no recovery executed.**

## Current selection and blockers

Prompt 09 selects the existing HF dataset `edithatogo/corpus-legislation-nz`.
The candidate package SHA-256 is
`2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c`
(71,776,346 bytes), built at source commit
`abb3d673bb8a082b9c0c8bdf5bb8bfbd3ac91ebe`.
These values come from the reviewed Prompt 09 receipt, not a fresh retrieval.

The live HF revision `1efa35e72c378068cfb112d060bd0502497f61b1`
listed 112 paths and no `durable-state/` paths during this audit. It is a metadata
observation revision, **not a published package revision**. The expected path is
`durable-state/v1/<package SHA-256>/state.zip`. Payload rights remain blocked;
there is no exact package publication/access receipt. PR #324 remains unmerged.
Do not upload, relax access controls, reuse a retained local package, substitute
an Actions artifact or call the earlier local round-trip this drill.

## Execution protocol after prerequisites are satisfied

1. Authenticate the approved package reference separately from the download:
   dataset identity, full Git revision, exact path, size, SHA-256, source/build
   commit, inner input pins, rights/access decision and publication/readback
   receipts. Re-evaluate the reference if any bytes or rights declaration change;
   the current candidate digest must not be silently reused for a new package.
2. Pin the merged software revision and locked environment. Create a new private
   temporary workspace with an exclusive owner marker. Record its empty inventory
   before retrieval: no manifest, checkpoint, CAS, package or Actions cache. Keep
   logs and receipts outside that disposable directory. Record OS, Python, uv,
   lockfile hash, helper hashes, Git SHA, UTC times and exact command exits.
3. Retrieve the exact file from the selected HF repository at the full revision,
   using its supported download path and a new empty cache. The revision-specific
   URL is `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz/resolve/<revision>/durable-state/v1/<digest>/state.zip`.
   Use only legitimately available access; stop on missing bytes or an access
   gate. Never log tokens, authorization headers or redirected signed URLs.
   Enforce the approved size and package bound while downloading, write
   exclusively, then recompute SHA-256. Preserve failures; no automatic fallback.
4. Run the reviewed Prompt 09 `verify` command with the independently pinned
   digest and an absent output receipt. It checks canonical outer encoding,
   indexed sizes and SHA-256/BLAKE3, inner state/parent pins and semantic roots.
   Only after success run its `restore` command into an absent destination.
   No command may use canonical repository state or retained original packages.
5. Recompute comparisons from the restored bytes, not from receipt prose:
   manifest root, checkpoint file SHA-256 and internal inventory root, all CAS
   objects and both hashes/sizes, distinct work/expression/manifestation counts,
   reviewed seed or discovery inventory hashes, parent descriptors/archive hashes
   and source commits, rights/access declaration. Compare every original indexed
   file. Preserve a per-field expected/observed/match report. Do not equate record
   count with expression or manifestation count. The merged 552-work inventory
   is not the 500-ID reviewed seed or the 33,693 search candidate universe.
6. Run `tools/run_legislation_reconciliation.py` with explicit restored manifest,
   checkpoint and CAS paths and a new receipt path outside restored state.
   Do not supply a candidate-denominator override. Require zero unexplained
   mismatches and schema findings; retain any failing receipt unchanged.
   `tools/run_legislation_recovery_drill.py` may additionally verify reconstruction
   from this restored state, but cannot by itself establish remote custody,
   package lineage, all scope metadata or an independent remote retrieval.
7. Perform a no-write continuation preflight using Prompt 08's reviewed source
   and parent-authority contracts. Hash the restored inventory before and after;
   require equality and no acquisition/publication. A canonical merge has no
   native harvest receipt merely because it has been packaged. If the required
   adoption authority is absent, report a blocker; never fabricate a receipt,
   relabel merged state as a native continuation or dispatch an acquisition lane.
8. Seal logs, comparison reports, reconciliation, environment and parent-preflight
   receipts outside the test workspace. Verify those evidence copies first.
   Remove only the disposable directory created for this attempt after proving
   its owner marker, exact path and absence of shared mounts or symlinks. Retain
   failed quarantines as evidence unless separately authorized for disposal.
9. Repeat from a second fresh workspace and fresh download cache, preferably a
   different environment. Fetch the same exact remote revision again; do not copy
   the first package or CAS. Compare both root/count/object inventories. Record
   whether independence is workspace-only or also machine/operator independent.
   An unavailable second environment or repeat is an explicit limitation/blocker,
   not an invented second success.

## Command interfaces

Once Prompt 09 is delivered, use its exact pinned software and these interfaces
with absolute, attempt-specific paths. Placeholders must be replaced from the
approved reference; these examples have not been executed by Prompt 10.

```text
uv run --locked python tools/legislation_durable_state.py verify --input PACKAGE --digest EXPECTED_SHA256 --output NEW_VERIFY_RECEIPT
uv run --locked python tools/legislation_durable_state.py restore --input PACKAGE --digest EXPECTED_SHA256 --output ABSENT_STATE_DIRECTORY
uv run --locked python tools/run_legislation_reconciliation.py --manifest-path RESTORED_MANIFEST --checkpoint-path RESTORED_CHECKPOINT --cas-path RESTORED_CAS --receipt-path NEW_RECONCILIATION_RECEIPT
```

Do not invent a generic successful continuation CLI: parent adoption is a distinct
reviewed authority prerequisite. Add narrowly scoped tooling and regression tests
only when a real published package and its authority contract can be exercised.
A package-format defect requires a separate fix commit and regression test.

## Evidence and completion

The initial blocked receipt is
`evidence/migrations/corpus-legislation-nz/durable-recovery/preflight-20260831.json`.
Add later attempts as new records; do not overwrite it. Keep statuses separate:
prerequisite audit, retrieval, verified fixity, restoration, reconciliation,
parent preflight, independent repeat and final acceptance. Two complete attempts
with matching roots/counts and zero unexplained mismatches are required. Neither
a green documentation PR nor a local packaging test completes Prompt 10.
