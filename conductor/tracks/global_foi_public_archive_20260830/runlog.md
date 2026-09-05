# Run log

## 2026-09-06 — Isolated local FOI continuation

Read canonical Conductor implement/review contracts and repository workflow.
Reconciled PR #403 against requested base `c5233ae7`, then implemented P2.5,
P2.6 and P2.7 in separate local commits. Red cases: 7, 7 and 5. Final FOI suite:
483 passed; changed modules: 100% line/branch coverage; seven guard mutants
killed. Full harness: 4810 passed, three unrelated timing failures; all three
passed the single isolated diagnostic rerun. Full certification remains open.
Commands, precise limits and receipts: [review](local-safe-gaps-20260906.md),
[machine record](local-safe-gaps-20260906.json). No global registry edits,
push, publication or ownership transfer. Other worktrees preserved.

## 2026-08-30 — Draft preparation

- Read the invoked conductor-newtrack skill and its common/new-track contracts.
- Read project context, workflow, autonomy, prior federation/ownership boundary,
  existing publisher/registry paths and current automation evidence.
- Queried failed hosted steps and exact lease-owner terminal state; no workflow
  dispatch, state edit, upload, credential change or donor modification occurred.
- Created isolated branch `codex/foi-public-archive-track` at receiver baseline
  `5eda36dd2d204a6a859100f913b411c44a08bf62` to preserve active health work.
- Ran full Conductor validation; retained legacy errors. Repaired only missing
  VCS/archive handshake links and added a summary of existing Git policy.
- Setup validation then passed. Prepared a proposed contract with ownership
  decision pending and separate readiness/corpus-completion criteria.
- Initialization commit and implementation await the required contract approval.

## 2026-08-30 — Approval and track initialization

- User approved the specification, plan and archive-govt-nz takeover while
  retaining fyi-cli; recorded the exact response and reviewed draft hashes.
- Preserved the draft evidence event; append approval/refinement evidence.
- Added a dated ownership supersession without deleting the prior requirement
  or rewriting historic completion. Updated the product roadmap prospectively.
- Incorporated artifact-expiry rescue, coherent public snapshots, cross-repo
  owner fencing, cold restore, hostile-input quarantine and resource budgets
  into existing acceptance criteria and TDD tasks; no new provider or spending.
- Scope of this commit is approved track creation. Production execution tasks
  remain pending; no donor workflow/state or public data was changed.

- Approval validation: setup and selected-track checks passed; evidence chain and all 12 acceptance IDs checked. Full validation still reports 172 legacy errors and zero additional errors. `git diff --check` passed.
- Evidence append initially rejected an absolute ledger path; corrected once to the required project-relative path and both events validated.

## 2026-08-30 — Implementation start

- Selected the explicitly approved global FOI track, not the unrelated active health track. Receiver remote main remains 5eda36dd2d204a6a859100f913b411c44a08bf62; donor main remains cba7b0dec2734bdc9ff51c69610fc55cb1fc5aa1.
- Full generic Conductor preflight reproduces the 172 known failures; investigating parser/legacy-schema compatibility before production changes. No isolation-lease mode is enabled; work remains in the dedicated clean worktree.

## 2026-08-30 — implementation baseline and compatibility audit

- Isolated receiver worktree at 5eda36dd2d204a6a859100f913b411c44a08bf62 and donor worktree at cba7b0dec2734bdc9ff51c69610fc55cb1fc5aa1; original dirty checkouts preserved. Initialization 0529e5f; in-progress transition 68818aa. Approval remains effective.
- Parent issue #233 and eight nested phase issues #234–#241 created; exact links in github.json.
- Generic full validator baseline has 172 historical errors. A supplementary native-format audit reads numbered registrations and legacy observations without rewriting evidence; 68 track records examined. Historical prose plans are byte-pinned and do not acquire fictional task checkmarks. Generic validation success is NOT claimed; P0.2/P0.4 remain open until reconciliation is complete.
- Initial test collection failed because tools was not importable; corrected test path setup. Boundary regression run then produced two expected failures (inline registry links and malformed gate containers); after correction all 13 tests passed. Ruff and scoped basedpyright passed.
- Required ./scripts/validate.sh invoked; results recorded when complete. Do not confuse this code gate with full generic Conductor compatibility.
- Donor failed owner run 31929819944 has zero retained artifacts according to GitHub API. No active state, source capture, or Hugging Face publication was changed. Local recovery preparation may proceed, but AC12 prohibits production implementation commits until the blocking baseline is reconciled.

### Baseline reconciliation completed

The canonical full validator now returns zero errors across 69 records (68 existing track records plus the imported snapshot container catalogue). Numbered and child registry entries now use the canonical Track prefix. Metadata aliases and equivalent UTC timestamps were normalized; missing creation timestamps state their Git-derived basis. Original prose plans remain verbatim in plan.original.md (13 hashes verified against 5eda36d). New preservation checkboxes describe preservation only and do not assert historical task completion. Three unchained legacy ledgers retain their original bytes and explicit format/hash declarations; the supplemental audit validates them rather than pretending they were canonical chains. Neither imported donor tree was changed.

The initially proposed legacy-plan bypass was removed in favor of explicit original-byte preservation and canonical navigation. A red regression caught modified legacy evidence not being detected; hashing now rejects drift. Full Conductor validation and the supplementary audit both pass. The supplementary audit is added to the required harness after lock validation; the stage-order regression was first observed failing and then passed.

./scripts/validate.sh completed successfully on the reconciled code: 1,362 tests, 95.72% combined coverage, schemas, parity, mutation lanes, hygiene, CAS benchmark, dependency/license/secret checks and SBOM. A lint failure during an intermediate run was fixed by using object instead of Any in the observation reader. Generated timestamps in unrelated evidence files were restored after the harness; no source or existing historical evidence bytes were replaced. Full results and output digests are in phase-0-validation.json.

Live inventory: 23/23 Hugging Face repos anonymously public and ungated, 29 sites, 42 regimes (39 blocked, 3 unsupported). NZ state remains 17,225 credited of 33,208 (15,983 remaining), held by failed run 31929819944. Audit of 218 artifact pages yielded 21,730 unique metadata entries: 21,724 retained (1,848,706,100 bytes) and six expired. No retained artifact expires within seven days. This is artifact-container volume, not a verified raw-corpus byte count. No payloads downloaded, no issue state repaired, and no publication/cutover performed.

## Hosted baseline correction

PR #244 exposed concurrent append-only health observations. Fix `e92845b` pins the original evidence byte prefix without freezing new entries. Integrated current main; full harness passed 1498 tests and 95.95% coverage. Corrected hosted checks remain pending. Receipt: phase-0-ci-correction.json.

## Active-owner repair and country catalogue

Merged donor repair PR #403 after exact-head green hosted checks. Merge: b6e78703d871082433fb33f8fa610761c2eb4062. Dispatched diagnosis-only recovery run 33305391040; no queue mutation is claimed. Implementation and tests for P1.1-P1.4 are complete; P1.5 hosted recovery/public readback remains open.

Committed source-catalogue foundation c1bf57b and integrated the corrected baseline/latest main in 248dd39, preserving both FOI and health schema registrations. The local candidate contains entities.jsonl, sources.jsonl, jurisdictions.jsonl, coverage.json, coverage.md and manifest.json. P2.1 is complete; P2.2-P2.3 remain in progress because country source assessments and public delivery are not done. Publication and takeover remain pending. The donor's separate AU/NSW private-retention destination stays private.

Hosted recovery 33305733977 succeeded: exact failed lease released, credited coverage unchanged, next offset 17225. One-request/no-continuation capture 33305989413 is queued. Full catalogue harness passed 1522 tests, 95.98% coverage, all stages. Legacy HF publication evidence fabrication was discovered during publisher selection; isolated fail-closed correction is under validation on codex/foi-publication-guard, not treated as real delivery.

## Raw-retention and publication-evidence checkpoint

Baseline PR #244 merged after exact-head green checks. Capture 33305989413 succeeded but downloaded artifact 9730497676 lacked the original capture directories. NZ monitor 322525555 is disabled_manually. Donor #404 adds raw-file/WARC verification and fresh artifact restore before credit (917 tests, 93.39% coverage locally); hosted proof remains pending. HF summary dry run 33306106031 passed without a public upload. Receiver #247 prevents fabricated publication receipts (1499 tests, 95.94% coverage locally). Country completeness, durable public storage and takeover remain unverified. See operational-followup-20260830.json and publication-guard-validation.json.

## WARC container and late failure handling

PRs archive-govt-nz#246/#247 and fyi-archive#404/#406 are merged. Follow-up capture 33307488567 failed before credit because the pinned adapter writes multiple WARC records within one gzip member. No artifact survived that failure; exact recovery 33307589477 cleared only its lease and preserved credited offset 17226. Donor #407 adds bounded whole-container parsing and moves failure retention/release after verification. Local validation passes 921 donor tests (one skip, 93.40%) and 1522 receiver tests (95.98%). Hosted restoration remains pending. No matching local Codex automation configuration referenced either repository; GitHub NZ monitor remains disabled. Details: container-recovery-20260830.json.

## Bounded original-byte restore passed

Donor #407 merged at be992fe036d5a270e228b5277e5b5770b9950ad8 after exact-head green checks; merged tree matches the tested branch. One-request run 33307777685 passed capture, raw verification, upload, clean download and verification before credit. Local independent download verified all seven inventory files (49,405 bytes, two WARC responses); its raw manifest hash matches both batch evidence and the issue receipt. This sample had no attachments; compressed attachment preservation is tested locally, not newly established by this live sample. Installed fyi-cli is 1.2.1.

Queue credit is now 17227/33208, leaving 15981 unprocessed entries and zero active leases. The 41,602-byte artifact expires on 2026-11-28; temporary retention is not durable HF storage. Monitoring remains disabled until source eligibility, durable retention and historical raw gaps are reconciled. No additional public HF upload, country-completion claim or cutover occurred. Receipt: hosted-raw-restore-20260830.json. All phase-level acceptance gates remain as listed in plan.md.

## Continuation — 2026-08-31

Resumed under the existing public-archive authorization from merged receiver 97ae6067d7320fe634f5e202219c412cf4ba754a. Both Conductor validators pass (69 records, zero errors). NZ queue is unchanged at 17227 of 33208, no leases, monitor disabled. P1.5 public readback depends on P3/P4; P2 endpoint rights remain unresolved. Continue the unblocked P3.2/P3.3 immutable-package and metadata-index work, retaining explicit publication gates. Original health checkout remains untouched.

## Local immutable package verification — 2026-08-31

Implemented CAS-backed preservation of original capture files and stored WARC response bytes, JSONL/Parquet object/request/event/resource indexes, deterministic raw tar packaging, and isolated cold restoration with rebuilt-index comparison. Package CLI requires an independently trusted inventory or manifest hash and never uploads implicitly.

Focused checks: 78 passed; critical module line and branch coverage 100%. Four integrity mutations killed. The first mutation harness attempt rejected a non-unique target before mutation; narrowed the target to unique context, reran successfully, and corrected the resulting string-format lint finding. Native schemas: 35 schemas and 25 documents passed. Full harness test stage: 1600 passed, 96.11% coverage; supply-chain stages still running when this entry was written.

Live retained NZ sample: original inventory, one request, two events and two response bodies restored and reindexed identically. No raw payload was committed or uploaded. Source policy observations are separate from redistribution clearance. The adapter's silent skip of attachment HTTP 404 is an additional completeness gap; explicit missing-attachment accounting remains required before resuming dispatch.

Full `PYTEST_XDIST_AUTO_NUM_WORKERS=2 ./scripts/validate.sh` completed with exit 0: 1600 tests, 96.11% coverage, all integrity/mutation, schema, dependency audit, licence, secret and SBOM gates passed. Post-run Ruff/format checks passed for the final mutation harness correction. Receipt: local-package-validation-20260831.json.

## Attachment-gap accounting — 2026-08-31

The adapter inspection found silent HTTP 404 skips. Red tests observed missing module/index output and six accepted index-tampering cases. Added bounded HTML/JSON/resource attachment census with retained/not_retained states, unknown HTTP status and unambiguous event links. Version 2 packages include JSONL/Parquet attachment indexes; version 1 restoration remains supported. Cold restoration rebuilds the census; envelope verification also rejects fabricated or missing attachment relationships. Focused validation passed 99 tests with 100% line/branch coverage across both critical modules. Full harness and donor queue-credit guard are the next checks.

Full attachment harness completed with exit 0: 1621 tests, 96.15% coverage, all quality/schema/mutation/supply-chain gates. Six focused integrity mutants killed. Live v2 cold restore and existing v1 verification both passed. Receipt: attachment-package-validation-20260831.json.

The staged-source secret scan flagged the intentionally synthetic Basic Auth rejection fixture. Added the same narrowly scoped synthetic-fixture annotation already used by catalogue tests; no production credential or scanner rule was changed. Re-running the staged scan before commit.

Latest-main integrated validation and PR 258 CI stopped at Ruff E501: the synthetic secret annotation made one fixture line too long. Shortened only the fake credential value, preserving the rejection test and scoped scanner annotation; rerunning the full gate.

## Verified public delivery foundation — 2026-08-31

P4.1/P4.2 implementation adds a distinct eligibility boundary for the safe catalogue and exact source-specific raw decisions, immutable snapshot paths, anonymous fresh-cache downloads, content verification, cold reconstruction, and conditional current-pointer/card promotion. Dataset cards expose separate index tables; viewer readiness remains a separate observation.

Observed red cases included missing transport, absent public card, malformed review references accepted past the intended gate, and a local receipt race that overwrote another receipt and concealed remote outcome. Corrected each with bounded tests: raw eligibility fails before writes; publication exceptions are sanitized; receipts use exclusive creation and report already-verified remote state separately when local saving fails. Original raw decision inputs are not generated or approved by the agent.

Four transport integrity mutations were killed. Focused critical coverage was 100% across transport, SDK boundary and publication guards before the final command/schema checks. Full harness is now running. Foundation PR 255 merged at d37b72e7dbcabad82c68f378ff07274411a7850a after integrated validation (1655 tests, 96.18%) and exact-head green checks. Attachment PR 258 merged at a17b0fda7b4f2ba4f71023ed4e118b7d292c14bb after corrected integrated validation (1676 tests, 96.20%) and green checks. Donor PR 408 has one preview-encoding correction awaiting renewed hosted checks. No public upload or monitor activation has occurred.

Publication full harness attempt 1 reached 1724 passing tests but stopped on Hypothesis input-generation timing in the existing URN property test (no assertion counterexample). Recorded seed 7018757617877908458207565406650075635 passed both URN properties unchanged. Retry uses one test worker after donor validation completed; no health check or test threshold is suppressed. Bounded log: /tmp/foi-delivery-full-validation.log.

## Verified public catalogue — 2026-08-31

Published the approved source metadata catalogue to edithatogo/foi-source-catalogue. Fresh anonymous downloads verified all snapshot bytes before conditional current-pointer promotion. Raw source payloads were not published. Donor #408 merged with exact-head green checks. The second full local receiver gate recorded a subprocess timeout and a Hypothesis generation health check in unchanged tests; the latter passed with its exact seed, while the subprocess still timed out. Host load exceeded 300. No checks were weakened. Hosted receiver assurance remains required. Receipt: public-catalogue-delivery-20260831.json.

Reviewed directory update: 30 known sources, 251 entity review rows, 23 directory-listed entities. All unknown request totals stay null. Snapshot 512fb25519fc1002c411fbcc37f04bb176f0b03c anonymously restored before current promotion. Focused integrated validation: 180 tests, 100 percent critical-module coverage. Original donor seed bytes and historical Argentina identity remain unchanged. Broader country discovery remains open.

## Receiver metadata automation — 2026-08-31

Preparing a main-branch-only weekly/manual catalogue workflow with one scoped
credentialed command, fixed concurrency, twenty-minute budget and always-retained
sanitized result receipts. It never accepts a raw-publication decision or starts
source acquisition. Hosted execution remains pending; donor NZ monitoring stays
paused. This is catalogue monitoring only, not completed P5 acquisition or P6
ownership transfer.

Workflow validation first stopped on the test's YAML loader lint rule. Replaced
BaseLoader with safe_load and explicit YAML 1.1 boolean-key assertions. Actionlint
and the workflow boundary test pass. The corrected full harness is running; this
is not a hosted execution receipt.

## Hosted catalogue retry correction — 2026-08-31

Receiver publication PR #262 merged at 071e9541ee6e16771f417afa6b7cc4debc9e7483;
all three hosted platforms passed 1824 tests. Metadata workflow PR #264 merged at
78cd8fa732af55ea40b7595804f894ce7ea9c5e8 after green hosted assurance.
Its first manual run 33357695865 failed safely and retained a failure receipt.
A regression using the real catalogue projection reproduced remote_integrity_failure
on an unchanged retry: canonical pointer JSON sorted table keys, while card
configuration ordering followed the original insertion order. A single fixed
table order now regenerates the same existing public card across pointer round trips.
No immutable public bytes or raw source data needed replacement.

Added allowlisted diagnostic reason codes; arbitrary exception text remains
redacted. Twenty-seven focused delivery/CLI tests pass, with 100 percent delivery
statement and branch coverage. Hosted retry after the correction remains pending.
The prepared NZ publication decision stays explicitly pending; no rights/privacy
approval has been supplied or fabricated.

## Receiver metadata verified — 2026-08-31

Retry PR #265 merged at 3d557bcf9cc9b86945f97e3340d9d6a9d0e0fd44 after all hosted checks passed. Run 33358508220 completed successfully; its downloaded receipt matches manifest 42d003245024432140ba2070c998c32779bbb587516bf0c62aeb32085c6a1558 and current revision 4e5a7832f6536e231d20292c1bffaae7861fd912. No new bytes were uploaded. The weekly metadata workflow is active. Raw acquisition, donor ownership and all source rights/privacy gates remain unchanged. See hosted-catalogue-verification-20260831.json.

The corrected full local harness completed successfully: 1825 tests, 96.34 percent
coverage, schema/parity/mutation gates, dependency audit, licence inventory,
secret scan and validated 111-component SBOM. Earlier timing failures remain in
the evidence history. Final track reconciliation passes 70 records with no errors.

### 2026-08-31 — durable control continuation

Resumed after evidence PR #267 merged; recovered a clean continuation worktree
from main while leaving the unrelated health worktree untouched. Used all three
available subagents for source evidence, scheduling, ownership and cross-review.
Implemented local durable state, strict queue reconstruction, exact owner/version
transactions, bounded scheduling and parity/transfer proposals. P5.1/P5.2 and
P6.1/P6.2 remain partial; no hosted owner authority was deployed.

The metadata workflow is active and latest observed run 33358508220 succeeded.
Donor monitor 322525555 remains disabled. Canadian nil-return evidence and verified
single-disk sample preservation are recorded separately. No raw publication,
source activation, source-specific approval, country completeness or cutover is
claimed. Final integrated validation is recorded in the continuation receipt.

Three full local gate attempts reached the unchanged 300-second test-stage limit. The final cache identifies the existing legislation order-invariance test for isolated diagnosis; no full-pass claim is made. Hosted validation remains pending. A new factual-context NZ v2 candidate was fully verified and cold-restored locally; its distinct manifest is recorded in raw-candidate-reconstruction-20260831.json. It does not inherit the older pending decision.

PR #272 hosted Ubuntu passed 2,048 tests, 96.84 percent coverage and mutation stages. The gate then rejected two non-secret provider hash strings in the Canadian projection. Omitted unused unverified provider hashes while retaining original metadata and its SHA-256; no scanner exemption. A new pending decision binds only the reconstructed 351465 candidate; the historical a78bef decision is unchanged.

## 2026-08-31 — Shared execution and country capture continuation

- User explicitly authorized autonomous deployment and expanded capture, requesting grouped permissive rights/privacy recommendations afterward. No public raw eligibility decision was supplied.
- Resumed from merged PR #272 at 33ad03e1204d4b8b4622b8a28dc43c12490857ed in an isolated clean worktree; branch codex/foi-shared-execution. Three agents own shared Git state, dispatcher/workflow, and bounded country pilots/rights groups.
- GitHub Actions enabled; default token permission read, job-scoped write is required for control state. No repository rulesets observed; privileged out-of-band ref modification remains outside CAS protection. No hosted settings changed.
- Initial Conductor command incorrectly used a nonexistent repository-local validator; corrected to the installed Conductor validator. Baseline reported five pre-existing RIOPA canonical-navigation/UTC errors. Exact UTC normalization exposed a pre-existing update-before-creation inconsistency. Preserved the original recorded timestamp, recorded this current metadata repair time, and fixed canonical links/status only. Full Conductor validation then passed. No historical evidence was changed.
- Rollout test red: new module absent (collection failure); green: three tests, 100% line/branch coverage. Ledger represents all 251 entities and 30 sources, no acquisition/publication activation and no completed-country claims. Lint caught one CLI line length, corrected by formatter.

- Shared-backend agent validated 33 new tests plus 21 queue regressions, 100% critical coverage, and four killed mutations. Root independently reran 33 backend tests and reviewed the state model.
- Added `record_capture` with a terminal local-only state: 48 scheduler tests, 100% line/branch coverage; seven existing/new local-control mutation probes killed. Focused queue/scheduler/rollout regression: 72 passed. Test lint/type findings were corrected; no verification threshold reduced.
- Root independently hashed and compared six original files across the CA and US pilot/cold-restore directories. Both manifests match their recorded identities. Original bytes remain outside Git on one private local disk. This proves bounded local retention, not independent replication or public durability.
- Independent review identified a missing CKAN success-envelope check in the CA adapter; correction and hostile-input bounds are being integrated before full validation.

- First full harness passed 2,266 tests at 96.95% coverage, all mutation lanes,
  schemas/parity, audit/licences and secret scanning, then timed out (124) on
  final SBOM generation at its unchanged 300-second cap. Full pass is not claimed.
  One isolated 60-second diagnostic located the wait in the CycloneDX subprocess;
  environment diagnosis continues with no scanner/gate exemptions.
- Preserved test-generated evidence diffs outside Git, then restored only the
  four named unrelated generated receipts. Saved the entire scoped work in stash
  e97ff79380010ebf13811251f6a9b8751f9b66eb and a separate binary patch before
  fast-forwarding to current main 565dd8845d151dcd31e5b6448e719f05fa12011d.
  Applying the exact saved stash produced two RIOPA rename/content conflicts.
  Preserved upstream archived completion, current UTC metadata and all historical
  evidence; retained only four canonical link-label corrections in the archived
  index. Full Conductor validation passes. The saved stash remains available.

- SBOM timeout isolated to duplicate strict validation using the locked IRI parser. A generation-only pass followed by the required strict schema/format validation completed in 135.088 seconds, within the unchanged 300-second bound. No dependency, schema or format checks were removed. The complete combined-main gate remains pending.
- The generic evidence append helper rejected a historical UTC `+00:00` timestamp. Used repository-native chain validation plus the canonical new-entry constructor and ledger lock to append the failure receipt; historical ledger bytes were preserved exactly.

- The combined-main full gate returned 124 at the unchanged 300-second test bound. Its child completed with 2,312 passing tests, 96.96% coverage and two timing failures (Hypothesis input generation and a nested negative-control pytest timeout) in 318.48 seconds. These are retained as failures, not a full local pass; focused repeat and remaining-stage validation are separate evidence. Hosted full assurance must pass before merge.

- Both failing timing tests passed in isolation with the exact Hypothesis seed (2 passed in 31.19 seconds), without source changes or relaxed checks. This does not replace the failed full-gate result. The remaining-stage run passed schemas, parity and two mutation lanes, then lost access to the workspace during mutation-redundancy. The workspace subsequently became accessible; no permissions or access controls were changed.

- PR #288 required integration of newly merged main d6bc0c9 (lineage and health delivery). Resolved the additive supply-chain-test conflict by retaining both upstream secret-adjudication tests and the new strict-SBOM regression. Stopped only this worktree's remaining-stage validation before integration; its partial log is not a full pass.
- The newly merged final-lineage track also required three canonical navigation-label corrections for the generic full Conductor validator. No imported snapshot, acceptance or historical evidence was changed. All 13 integrated supply-chain tests passed.

- Hosted run 33394282528 passed Linux (2,390 tests, 96.98% coverage, strict SBOM) and macOS. Windows failed two POSIX-mode assertions and setup/teardown for an oversized pytest parameter ID. The correction keeps every functional case, uses bounded test IDs and distinguishes POSIX modes from unverified Windows ACL privacy. No failed-platform merge or deployment occurred.

- PR #288 merged at 9c609fe after all seven corrected-head checks passed; each platform passed 2,390 tests. The merged tree matches the tested tree. Only the queued bootstrap run was cancelled, and the authority was confirmed absent afterward. Tested local processes created the GitHub authority, proved persistence, and exercised a real same-parent race (HTTP 200 versus 422). Existing state was preserved.
- The Canadian shared executor preserved and cold-restored the expected manifest, recording captured without public credit. Anonymous health passed. Subsequent hosted writer run 33397203569 and read-only health run 33397451283 passed; their final authority revision agrees. Daily 04:41 UTC health is active, but no scheduled cycle is claimed observed.
- Both CA and US private packages have a verified replica on the internal disk, separate from the external USB source disk. No raw data was published. Country completeness remains zero verified and donor cutover remains false. Grouped publication options are presented, with policy approval and publication enforcement still open.

- Separate post-merge run 33396086444 passed Linux/macOS but Windows exceeded the unchanged five-minute test-stage limit at 88% without a functional failure report. The already-supported two-worker loadscope lane is selected for CI to reduce serial test time without suppressing tests, coverage, health checks or stage bounds. Live control writer/health outcomes are unaffected.

- The deployment-evidence local harness returned 1: 2,388 passed, two timing failures, 96.98% coverage in 188.38 seconds. Acceptance timeouts now produce a failed sanitized receipt (no retry, no evidence hash). The manifest property retained its default deadline; binary-to-hex generation reduces earlier input-generation overhead but cannot prevent host scheduling delays. Four acceptance regressions and the prior-seed property passed separately. The corrected full gate is running; no full local pass is inferred.

- Corrected full local harness passed every stage, including strict SBOM: 2,393 tests, 96.98% coverage, 116.49-second test stage. Subsequent review found cross-module writes to shared preservation and archive-ledger receipts; explicit output destinations isolate those tests before CI parallelism. These later isolation changes and newly merged main require separate validation and are not included in the 2,393-test claim.

- Integrated main through 25f9fb5 without conflicts, preserving upstream health and legislation work. Generic Conductor validation found newly imported link labels, `complete` versus registry `completed`, and calendar-only timestamps. Canonicalized labels/status without changing acceptance; retained original dates and used the first tracked commit time as the documented controller timestamp basis. Five output-isolation tests passed with two workers; Ruff/format/type checks passed.

- 2026-09-03: Ran the required `./scripts/validate.sh` on Python 3.14.6. Conductor validation, formatting, Ruff, basedpyright, 4,559 tests (97.50% coverage), schemas, parity, all configured mutation suites, hygiene, CAS benchmark (540.76 MB/s), dependency audit, licence inventory, secret scan, and 111-component SBOM all passed. This closes repository-owned P1.6 validation evidence only; it does not establish hosted acquisition, public raw publication, rights clearance, or donor cutover.
2026-09-05: User approved the recommended conditional standing policy. The policy is now recorded as approved with conditions: only official, non-personal institutional/statistical material may enter delegated admission; ambiguous rights, narrative correspondence, personal information, third-party material and drift remain quarantined. CA nil returns are the first candidate scope pending the required agent conformance review of the 162-organisation allowlist. US narrative material and NZ FYI remain private/metadata-only pending source-specific evidence. No public raw upload or cutover is inferred from this approval.
2026-09-05: CA organisation conformance review recorded in ca-organisation-conformance-20260905.json. The source-level licence, exact resource, schema screen and no-requester-field checks pass, but the 162-row organisation id/title allowlist is not materialized (only its expected count/digest are present). CA raw admission, public-only manifest generation and anonymous restore remain blocked pending that evidence.
2026-09-05: Retrieved the attributable public CA nil-return CSV and found 162 unique organisation id/title pairs, matching the expected count. The raw source hash and four documented canonical pair hashes do not match policy digest 74524ed8..., so the source remains quarantined pending digest-definition/revision reconciliation; no manifest or upload was produced.
2026-09-05: Reconciled the CA organisation digest to the live public source revision (6,226 rows, 162 unique pairs, SHA-256 6782abe3...). Conformance now passes for the live revision, while the older 6,191-row private pilot is explicitly marked for recapture. Publication remains ineligible until refreshed raw preservation, public-only manifest generation and anonymous restore complete.
2026-09-05: Recaptured the reconciled CA nil-return source privately at data/raw/ca-federal-atip/2026-09-05/ati-nil.csv (6,226 rows, 162 organisation pairs, 657,619 bytes, SHA-256 6782abe3...). Wrote ca-public-only-manifest-candidate-20260905.json. The candidate excludes private evidence files; anonymous restore and Hugging Face upload remain pending.
2026-09-05: Generated the CA public index (6,226 JSONL records) and manifest from the refreshed private package. Local restore/hash verification passed for CSV and index; ca-local-restore-receipt-20260905.json records the result. Provider-side anonymous restore after upload remains the next gate; no HF upload was performed.
2026-09-05: Published the approved CA files to public ungated Hugging Face dataset edithatogo/foi-ca-federal-atip. Anonymous direct downloads of ati-nil.csv, index.jsonl and manifest.json match local hashes. Dataset Viewer validation returned transient HTTP 500/busy and is recorded for retry; no private evidence files were uploaded.
2026-09-05: Rechecked public Hub state: repository is public at commit 59b2c321... and the Dataset Viewer parquet endpoint returns HTTP 200 with config conversion pending (rather than a dataset rejection). Direct anonymous restore remains the authoritative byte check until conversion completes.
2026-09-05: Dataset Viewer conversion was rechecked and now reports config-parquet failure for the public CA dataset. Direct anonymous bytes remain verified. Viewer-compatible representation diagnosis is required; no raw files were changed or removed.
2026-09-05: Viewer diagnosis found root manifest.json schema collision with index.jsonl. Uploaded README.md dataset card (commit 04292927...) selecting index.jsonl as default/train and documenting manifest.json. Immediate Viewer recheck was service-busy; direct restore remains verified.
2026-09-05: Removed root manifest.json from the HF data root after publishing the identical file at metadata/manifest.json; this prevents the Viewer from merging the object manifest into index.jsonl. Hub tree now contains only ati-nil.csv and index.jsonl at root plus documentation metadata.
2026-09-05: Hugging Face Viewer repair verified. Parquet conversion now exposes default/train with no pending or failed state; rows endpoint returns 6,226 total rows and sample data. CA publication and Viewer validation are complete.
2026-09-05: Added NZ metadata-only disposition receipt. It permits only non-sensitive source/package status metadata and explicitly excludes requester identity, correspondence, attachments, personal information and third-party material. Raw publication remains pending source-specific review.
2026-09-05: Hosted shared-controls run 33955611192 failed closed at health: one captured job remains unpublished, monitor_status attention_required, capacity/state healthy, and no state mutation occurred. Recorded in hosted-health-failure-33955611192.json; no gate was weakened.
2026-09-05: Reconciled captured job ca-federal-atip.nil-returns.20260831-1 with the current verified public CA package. Historical shared-state evidence remains immutable; current shared health must observe the publication transition on its next authority cycle.
