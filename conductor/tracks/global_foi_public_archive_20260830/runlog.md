# Run log

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
