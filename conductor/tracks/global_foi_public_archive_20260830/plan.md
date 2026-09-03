# Implementation plan — approved 2026-08-30

Approval and initialization are recorded in approval.json and evidence.jsonl.
Execution started on 2026-08-30; track status is `in_progress`. The order is TDD → implementation → refactoring → phase review/validation.
The approved destination is archive-govt-nz; no cutover has occurred.

## Phase 0 — Contract, baseline and traceability

- [x] P0.1 (AC01, AC12): Verify the recorded approval, ownership supersession and initialization commit against current donor/receiver state before execution; do not ask for routine reapproval. Verified against initialization `0529e5f` and activation `68818aa`.
- [x] P0.2 (AC01, AC12): Reconcile legacy Conductor validation errors without rewriting historical evidence; register the approved contract and create scoped parent/subissue links under the authorized repository workflow. Receipt: `0955f05`, phase-0-validation.json.
- [x] P0.3 (AC01, AC08, AC11): Pin donor/receiver/adapter/HF revisions; inventory capture capabilities, 23/29/42 registries, retained artifacts, raw bytes, queues, mirrors, rights and current jobs; prioritize expiring artifacts and record durable-copy gaps. Receipt: `0955f05`, phase-0-validation.json.
- [x] P0.4 (AC12): Automated contract review and full Conductor validation; retain exact baseline and unresolved boundaries. Receipt: `0955f05`, phase-0-validation.json.

## Phase 1 — Repair the active automation first

- [x] P1.1 (AC02): Write failing tests for the abandoned NZ lease, live owner, terminal success without receipt, stale observations and concurrent replacement. Local implementation: donor `85685a8`; hosted proof remains P1.5.
- [x] P1.2 (AC02): Implement evidence-bound exact-lease reconciliation, conflict-aware reservation and durable diagnostic receipts in the active owner; preserve completed coverage and requeue only uncredited work. Local implementation: donor `85685a8`; hosted proof remains P1.5.
- [x] P1.3 (AC03): Add failing CLI/workflow tests for concatenated JSON, diagnostics on stdout, missing summary, changed/unchanged runs, and cross-instance card data. Local implementation: donor `85685a8`; hosted proof remains P1.5.
- [x] P1.4 (AC03): Implement a dedicated schema-valid summary artifact, clean stdout/stderr contract, guarded card rendering and always-retained redacted failure evidence. Local implementation: donor `85685a8`; hosted proof remains P1.5.
- [ ] P1.5 (AC02, AC03, AC09): Verify repair in hosted runs, safe NZ progress past offset 17,225, public revision/card consistency, no skipped work and no runaway retry.
- [~] P1.6 (AC12): Automated review, active-owner required full validation harness, CI, and issue/evidence reconciliation; do not call local repair hosted recovery.

## Phase 2 — Complete source and country catalogue

- [x] P2.1 (AC04, AC11): Pin the country/territory universe and write failing coverage/uniqueness/seed-parity/rights-export tests. Implementation: `c1bf57b`; 23 focused tests passed.
- [~] P2.2 (AC04): Implement one registry and importer reconciling all 23 runtime instances, 29 sites and 42 target regimes; represent every country with reviewed sources or an explicit evidence-backed disposition.
- [~] P2.3 (AC04, AC09): Generate the public source index, machine coverage ledger and human report; keep unknown denominators null and states distinct.
- [ ] P2.4 (AC12): Automated review, schema/property tests and full phase validation.

## Phase 3 — Metadata indexes and immutable raw storage

- [x] P3.1 (AC05, AC06, AC11): Add red tests for original metadata preservation, request/correspondence/attachment relationships, revisions, missing objects, synthetic/CDX rejection, unsafe archive members, private-network redirects, expansion/resource limits, active content and sensitive exports.
- [x] P3.2 (AC05, AC06): Integrate pinned capture adapters, CAS/WARC packaging, JSONL/Parquet object metadata and complete provenance; reuse existing Bronze/storage primitives.
- [x] P3.3 (AC05, AC06, AC08): Implement durable checkpoint/package manifests and clean-room reconstruction; prove deduplication, interruption, temporary-artifact loss and corruption handling using bounded shards and stable IDs.
- [x] P3.4 (AC12): Automated review, integrity mutation tests, privacy checks and full phase validation.
- [x] P3.5 review fix (AC05, AC11, AC12): Reject unsafe initial capture URLs
  and redirect destinations before a request can reach a non-public network
  target; retain stable redacted failure evidence.
- [x] P3.6 review fix (AC12): Preserve the userinfo rejection regression while
  constructing its inert credential token in fragments so secret scanning does
  not misclassify test data as a live Basic Auth credential.

## Phase 4 — Public Hugging Face delivery

- [~] P4.1 (AC07, AC11): Add red tests for restricted publication, public metadata leakage, private/gated targets, wrong repo identity, partial upload, remote hash mismatch, inconsistent child revisions, provider outages and premature index promotion.
- [~] P4.2 (AC07): Wire public global catalogue, existing per-instance identities, raw payloads, metadata indexes, cards and revision-pinned manifests through the approved publisher.
- [ ] P4.3 (AC07, AC11): Reconcile source eligibility, platform capacity and least-privilege credentials; publish the eligible NZ candidate under recorded user authority and verify every accepted object anonymously.
- [~] P4.4 (AC07): Verify a second eligible instance, cross-instance isolation, revision-pinned catalogue links, interrupted-publication recovery, cold restore without cache and viewer status separately from raw storage.
- [~] P4.5 (AC12): Automated publication/security review, full phase validation and hosted receipts.

## Phase 5 — Sustainable acquisition for every country

- [~] P5.1 (AC08, AC09): Add red state-machine tests for fairness, per-origin limits, retry exhaustion, stale leases, missing artifacts, changed/withdrawn objects, byte/runtime budgets, fair queue service and blocked adapters.
- [~] P5.2 (AC08): Implement registry-derived schedules, historical/incremental queues, durable state and bounded continuation; do not use a blind country loop.
- [~] P5.3 (AC04, AC08, AC11): Walk the entire pinned country universe; assess all discovered sources, add bounded adapters where possible, verify capture/storage per eligible source, activate approved schedules, and retain explicit unsupported/blocked dispositions.
- [~] P5.4 (AC09): Add freshness/backlog monitoring and actionable stuck-state alerts; prove that green monitor execution cannot conceal failed capture/publication.
- [ ] P5.5 (AC12): Automated review, recovery/property/mutation gates and full validation with evidence-backed country counts.

## Phase 6 — Shadow parity, cutover and rollback

- [~] P6.1 (AC01, AC10): Add failing parity tests for cases, events, attachments, raw hashes, revisions, queues, checkpoints, retry, takedown behavior and delayed jobs from the former owner.
- [~] P6.2 (AC10): Reconcile shadow outputs using retained capture evidence without duplicate source load; exercise interruption, shared owner fencing, rollback and measured clean-environment recovery.
- [ ] P6.3 (AC10): Transfer scheduler/publication ownership to archive-govt-nz only after hosted parity and anonymous restore pass; record exact donor/receiver/HF revisions, the shared ownership fence and rollback window.
- [ ] P6.4 (AC10, AC12): Observe a successful scheduled incremental cycle, no duplicate dispatch and publication freshness; automated review and full validation. Donor deletion remains out of scope.

## Phase 7 — Final assurance and honest completion

- [ ] P7.1 (AC01–AC12): Audit requirement-to-test-to-receipt traceability, reproduce source/metadata/raw restoration, and reconcile every country and eligible source schedule.
- [ ] P7.2 (AC12): Run `./scripts/validate.sh` in archive-govt-nz and the active owner's required harness before any PR; verify exact hosted head checks and run automated Conductor review with bounded fixes.
- [ ] P7.3 (AC09, AC12): Publish verified system-readiness and corpus-progress reports separately; outstanding raw gaps prevent full-capture claims, and blocked countries remain explicit.
- [ ] P7.4 (AC12): Synchronize metadata, registry, issues, evidence and commit history only after the matching acceptance criteria pass; record continuing schedules and unresolved external limits.

## Critical operational findings

Bounded capture 33305989413 advanced the credited cursor to 17226, but its artifact omitted original bytes. NZ automatic dispatch is paused. Raw-retention PR fyi-archive#404 and fabricated-publication guard PR archive-govt-nz#247 are approved-scope corrective work while the remaining phase gates stay open. Details: operational-followup-20260830.json. No older raw coverage is retroactively verified.

Bounded original-byte restore passed in run 33307777685 after donor #407 merged. Credited next offset is 17227, with 15981 queue entries unprocessed. P3.3 remains in progress because durable storage, metadata reconstruction and historical raw-gap reconciliation are incomplete. Monitor remains disabled; see hosted-raw-restore-20260830.json.

P3 continuation: v2 packages add explicit attachment gaps and event relationships; v1 restore compatibility is retained. Donor credit must reject discovered-but-unretained attachment references. This does not prove exhaustive source discovery.

Hosted catalogue verification passed in run 33358508220 after retry-order correction. P4.4/P4.5 and P5.4 are partial for metadata only; eligible raw delivery, a second raw instance, acquisition monitoring and full phase acceptance remain pending. The next source-specific gate is documented in nz-publication-decision.pending.json. No raw or ownership gate is satisfied by the metadata run.

Local P5/P6 controls pass focused validation; see durable-controls-local-validation-20260831.json. The full gate remains pending after bounded timeouts. Strict owner/queue CAS, durable state and parity proposals are local foundations; production policy resolution, shared dispatch, quotas and hosted evidence remain required.

## Authorized deployment continuation — 2026-08-31

- [x] P5.6 (AC08, AC10, AC12): Deploy shared GitHub-backed control state, bounded cross-source reservations, live authority restart/conflict evidence and hosted writer/health checks; retain publication and donor cutover gates.
- [x] P5.7 (AC04, AC05, AC06, AC09): Produce every-entity rollout dispositions and verified bounded institutional-data captures with resource-specific denominators.
- [x] P4.6 (AC07, AC11): Present grouped, reusable rights/privacy publication options with exact candidates and exclusions; no approval inferred.
- [x] P7.5 (AC12): Repair pre-existing RIOPA canonical-link and equivalent UTC timestamp validation failures without changing acceptance or historical evidence.
