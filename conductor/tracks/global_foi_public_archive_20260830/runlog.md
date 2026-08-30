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
