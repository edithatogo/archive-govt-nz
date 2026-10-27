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
- [x] Task: Publish focused implementation PR #787 after passing supply-chain gates; unresolved external gates retained.

## P6: Hub metadata and collection hardening (user follow-up)

Issue: https://github.com/edithatogo/archive-govt-nz/issues/789

- [x] Audit 44 related datasets and four collections; preserve identity, original payloads and access gates.
- [x] Correct maintained cards, source-specific rights/coverage, compatible viewer subsets and collection membership; verify saved native revisions.
- [x] Publish a derived Parliament catalogue and anonymously verify all referenced source objects and 21 viewer rows.
- [x] Prevent default harvests overwriting a maintained card or a missing explicit card causing fallback replacement; remove fabricated schema/licence assertions.
- [x] Review metadata and source fixes; qualify affected tests and remaining assurance stages after intentional snapshot update.
- [x] Accept all14 hosted viewers after41 actual config/row probes; historical and RNZ faults repaired and isolated Python3.15 readers verified.

This completes metadata maintenance for the inspected estate, not missing source acquisitions, gates, rights clearances or full historical archival.

## Hosted assurance follow-up

- [x] Diagnose repeated Windows cancellation using native annotations; retain bounded evidence.
- [x] Apply and review bounded aggregate timeout/diagnostic remediation; Actionlint and21 focused tests pass.
- [x] Verify Windows and all required hosted checks at the remediation head before merge or further archive acquisition; PR787 merged9472eab7 after green required checks.

## Account scope and Windows recovery — 27 October 2026

- [x] Reconcile all public account datasets and aggregate private checks without exposing new private identities; parent-bound native registry publication and five anonymous pinned file hashes verified.
- [x] Complete remaining account viewers: 12 datasets and 33 config/split first-row probes pass; NHANES transient service-busy responses resolved without repeat writes.
- [x] Inspect actual Windows job log; shorten pathological oversized-robots parameter IDs and add an independently logged bounded gate runner. Targeted native acceptance remains hosted.
- [x] Run required local assurance and review the remediation: 8429 tests pass, all mutation and supply-chain stages pass.
- [x] Obtain all green hosted checks before merge; native delivery receipt `build/parliament/delivery-20261027.json`.
- [x] Resume bounded report batches after merge with publication recovery first, maintained card preserved and immutable originals retained; latest reviewed state798 originals plus1 metadata-only.

Account evidence: `../../../evidence/huggingface-hardening/20261027/`. Windows diagnostic evidence: `../../../evidence/parliament-assurance/20261027/`. Parent source rights, legacy access and natural schedule gates remain active.

Hosted follow-up: the integrated Linux run passed tests, schemas, parity, mutation, audit and licence gates, then identified a benign status sentence in the newly materialized local-assurance receipt as a Secret Keyword candidate. Reused the existing exact receipt pass-status convention and retained scope in a separate field; no scan policy/exemption was changed. Rerun only the affected secret stage locally, then require the full hosted candidate checks.

Final Windows candidate: complete collection inspection found a second auto-generated ID over four million characters. Both oversized-input cases now have short IDs while preserving their original bytes and fail-closed assertions. All 8553 collected node IDs fit the Windows environment-variable contract (maximum4186 characters); pytest writes these IDs to its current-test environment variable. Native preflight now selects the affected robots/API cases and real-child supervisor tests before the full gate. Fresh integrated local assurance passes all stages (8539 tests,14 capability skips); final focused cases and Actionlint pass. The earlier hosted run is superseded because it retains the second oversized ID and console-forwarding supervisor.

## Required hosted review fixes — 27 October 2026

- [x] Reproduce both unresolved P2 findings with failing regressions.
- [x] Defer budget-limited attachments without losing pending work; retain genuine per-file failures.
- [x] Bound discovery persistence before cursor admission, pass the shared spool policy through the worker/CLI, and stop further packaging at a full spool.
- [x] Review all affected source, run 80 Parliament tests and strict/static checks; kill both added budget mutants in the existing runner.
- [x] Complete full local assurance and require hosted checks on the corrected head, resolve addressed threads and merge without bypass; merged9472eab7.

Final account consistency: the public Hermes mixed-artifact archive's stale private/empty labels were corrected, preserving all174 published files and source terms. Final registry correction at `f82a1b706e7c55845ffef5dad0a1d4571b2892dd` was anonymously hash-verified. Source acquisition remains paused until delivery.


## P7: Continuous, batched and interruptible GitHub Actions execution

User-directed follow-up,27October2026. Contract: [hosted-execution.md](./hosted-execution.md).

- [x] Verify current local versus hosted execution, existing secret names, active writers and report/publication state.
- [x] Inventory report-only bootstrap:877 referenced objects already have verified public pinned references;119 unreferenced CAS objects explicitly excluded.
- [x] Define durable checkpoint, interruption, fencing, cold-restore and authority-handover requirements.
- [ ] Implement and test report-only projection, durable accepted-object/checkpoint protocol and shared writer fencing.
- [ ] Implement finite serial batch jobs with trusted-main workflow, explicit pause, concurrency, bounded disk and continuation.
- [ ] Run milestone assurance and Conductor review; fix findings and deliver through green required checks.
- [ ] Prove exact Actions HF binding, anonymous cold restore, cancellation/resumption and preserved card in a bounded native pilot.
- [ ] Hand over from local writers and enable scheduled continuation only after native proof; retain separate natural-schedule acceptance.

Latest local workset20261027T075911Z observed100 entries (page-one anchor, deep pages6–9, targeted late-attachment query and forward pages76–79);40new originals published and verified,798total originals+1metadata-only,0failed/0pending. Forward cursor80 and deep-reconciliation cursor10 remain separate. The known metadata-only report still has no attachment. Publication11eaae7bc65fae059f1770358daca78fae07f52af3d72cef00224d670ee07d36 at1c43e95e222ca0059276a7d1994b7714ca85dd7a. Runtime receipts and immutable originals remain on PortableSSD. Selective lane remains eight individually qualified author derivatives; existing holds remain effective. P7 is active work, not deployed collection.
