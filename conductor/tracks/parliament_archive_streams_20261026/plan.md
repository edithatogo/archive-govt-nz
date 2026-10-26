# Implementation plan

Implementation authorized on 26 October 2026; qualification in progress. Parent: [#778](https://github.com/edithatogo/archive-govt-nz/issues/778). Requirements: M1–M10, S1–S3, C1; exclusions W1–W3.

## P1: Source, rights and destination qualification

Issue: https://github.com/edithatogo/archive-govt-nz/issues/779

- [~] Task: Characterize legacy and new Parliament hosts, source IDs, filters, pagination, attachment links and source access rules using bounded read-only probes.
- [ ] Task: Reconcile the evidence and submissions/advice indexes by identity and filter scope; record historical coverage limits.
- [ ] Task: Record source-specific reuse/privacy handling and the exact existing Hugging Face destination, additive namespace and qualified write route.
- [ ] Task: Phase verification and evidence checkpoint under ../../workflow.md; use focused tests first, record local/hosted limits, run milestone assurance and recovery checks where applicable.

## P2: Durable discovery and streaming capture

Issue: https://github.com/edithatogo/archive-govt-nz/issues/780

- [ ] Task: Write failing focused tests for pagination drift, duplicate identities, crash recovery, rate limits, malformed links and incomplete downloads.
- [ ] Task: Implement versioned candidate shards, atomic checkpoints, partition leases and a bounded shared host request budget.
- [ ] Task: Implement streamed original-byte capture, hashing, atomic admission, failure queues, relationship metadata and changed/withdrawn observations.
- [ ] Task: Phase verification and evidence checkpoint under ../../workflow.md; use focused tests first, record local/hosted limits, run milestone assurance and recovery checks where applicable.

## P3: Pilot publication and independent recovery

Issue: https://github.com/edithatogo/archive-govt-nz/issues/781

- [ ] Task: Write failing tests for bounded packaging, interrupted upload, competing revisions and remote integrity mismatch.
- [ ] Task: Implement additive immutable object/catalogue batches with one shared catalogue writer and collection-specific rights metadata.
- [ ] Task: Capture one completed business item with submissions, supplementary files, advice and report context; reconcile all discovered outcomes.
- [ ] Task: Upload only eligible pilot content to the qualified destination; pin the remote revision and independently download, hash and reconstruct the pilot.
- [ ] Task: Phase verification and evidence checkpoint under ../../workflow.md; use focused tests first, record local/hosted limits, run milestone assurance and recovery checks where applicable.

## P4: Historical backfill and recent monitoring

Issue: https://github.com/edithatogo/archive-govt-nz/issues/782

- [ ] Task: Write failing tests for partition resume, overlapping recent windows, late releases, byte/time limits and shared throttling.
- [ ] Task: Configure separate historical and recent lanes with independent cursors and durable state beyond ephemeral runner artifacts.
- [ ] Task: Enforce proposed first-hit limits of 100 records, 250 MiB or 15 minutes, including per-file and spool bounds; tune only from pilot evidence.
- [ ] Task: Verify manual execution, interruption/resume, natural scheduled execution and remote recovery separately; report discovered/captured/failed/rights-pending/remotely-verified counts.
- [ ] Task: Phase verification and evidence checkpoint under ../../workflow.md; use focused tests first, record local/hosted limits, run milestone assurance and recovery checks where applicable.

## P5: Additional collections and final reconciliation

Issue: https://github.com/edithatogo/archive-govt-nz/issues/783

- [ ] Task: Qualify and add petitions/responses, papers presented, written questions/answers, Library research and procedural records as separate bounded source contracts.
- [ ] Task: Reconcile existing Hansard and legislation implementations and preserve contextual links without duplicate pipelines.
- [ ] Task: Separate optional text/OCR derivatives from originals capture; retain media archival as deferred pending endpoint, rights and volume qualification.
- [ ] Task: Run the repository harness and applicable security, package, coverage, mutation and recovery gates; complete self-review and reconcile GitHub, Conductor and hosted evidence.
- [ ] Task: Phase verification and evidence checkpoint under ../../workflow.md; use focused tests first, record local/hosted limits, run milestone assurance and recovery checks where applicable.

Scope control: phases are sequential acceptance milestones. Runtime streams become independently resumable after their contracts pass; this does not authorize competing writers or unlimited parallel requests.

## Implementation checkpoint — 26 October 2026

- [x] Report source/destination qualification and manually executed public pilot (see evidence.md for immutable receipts).
- [x] Focused synthetic contracts: durable queue, streamed capture, integrity, process-crash recovery, anonymous public publication and old-version metadata preservation.
- [~] Full repository assurance and Conductor review.
- [ ] Natural scheduled execution and periodic historical/recent reconciliation.

Original phase checkboxes remain acceptance milestones: P1/P3 are partial because submissions/advice lack source eligibility and a complete mixed business-item pilot. P4 needs natural schedule proof; P5 collections are not qualified through a denied legacy host. Do not archive this active parent or close its phase issues merely because the report implementation is delivered.

## Phase: Review fixes

- [x] Task: Apply provenance, source-contract, anonymous-publication and unknown-outcome recovery fixes f18c3ee7.
- [x] Task: Add isolated mutation guards for public visibility, anonymous download, remote fixity and robots policy; all four killed.
- [~] Task: Complete remaining supply-chain gates and publish focused implementation PR; retain unresolved external gates.
