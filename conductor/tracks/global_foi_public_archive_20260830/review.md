# Draft self-review

- Scope: covers source catalogue, original metadata and index, raw objects,
  public HF verification, global country discovery and the two observed failures.
- Ownership: unresolved DEC-FOI-001 is explicit; old separation rule is preserved.
- Authorization: public-HF intent is recorded; source rights and privacy are
  separate facts. No extra routine publication approval is invented.
- Integrity: keeps historical URL indexes, old manifest counts, real capture
  receipts, stored bytes and public verification distinct.
- Safety: no blanket lease reset, no progress skipping, no overlapping schedulers,
  no raw payload in Git, no donor deletion, no public release during planning.
- Tests: every implementation phase starts with acceptance-linked negative-path
  checks and ends with automated review and validation.
- Remaining: contract/ownership approval, legacy full-Conductor errors, all
  implementation tasks and external execution. This is not a completed system.

## Approval review — 2026-08-30

The user resolved DEC-FOI-001 and approved the contract. The pending-decision
findings above describe the original draft and are now resolved by approval.json.
Reviewed safety refinements are mapped to existing acceptance IDs in
recommendations.md and plan.md. No material new destination, purpose or cost is
introduced. Status `new` means approved and initialized, not yet executing.
Legacy full-Conductor findings remain explicit prerequisites for production
implementation; no historical completion is fabricated to pass validation.

## Phase 0 automated self-review — 2026-08-30

Result: passed for the baseline/traceability slice; later acceptance criteria remain open. Reviewed every changed metadata/index record by its normalization class, all 13 original-plan hashes against the base commit, untouched imported donor trees and original ledgers, the complete native validator and tests, source/HF inventory, sanitized artifact index, and harness integration.

Resolved findings: canonical registry parser missed numbered/child entries; missing links/specification pointers and archive container navigation; misleading canonical evidence-schema declarations on legacy records; unknown statuses/types and offset timezone spelling; absent drift protection for legacy bytes; validator crash on malformed gate containers; stdout/path-collision hazards in the separately prepared donor repair. No historical underlying task was newly marked complete. Style: general.md consistency/simplicity and python.md existing-style rule pass via repository Ruff and BasedPyright policy. Platform guide selection: not applicable (no platform-guide manifest).

Required full harness: pass, 1,362 tests, 95.72% coverage. Canonical Conductor full validation: pass, 69 records, zero errors; legacy-format warnings remain informative. Test and review receipts are in phase-0-validation.json. No source rights, hosted recovery, public payload completeness, country-universe completeness, or cutover claim follows from these results.

Operational risks: the donor ledger is still held by the failed owner, all target regimes lack final archive acceptance, the public HF repositories do not prove complete raw restore, and GitHub artifacts are temporary. The local recovery transition deliberately does not claim a remote compare-and-swap; hosted retention and serialized application must be wired and verified before applying it.

## Phase 1 / Phase 2 implementation checkpoint

Donor repair PR #403 merged at b6e78703d871082433fb33f8fa610761c2eb4062 after all non-skipped hosted checks passed. Local full tests passed 907 cases (one skip), with 93.38% overall coverage and complete measured coverage of the pure recovery and summary modules. Hosted repository-quality passed including Taplo; local full make quality remained limited by missing Taplo (the initially missing typos executable was subsequently supplied in temporary tooling). Diagnosis-only hosted run 33305391040 is queued; there is no recovery or new capture receipt yet.

Catalogue commit c1bf57b reconciles 23 runtime instances, six additional sites and 42 target regimes against 250 geographic entities plus EU. Reviewed all source projections, restricted-field omission, donor/universe byte hashes, alias preservation, nullable denominators, revision pinning, schema rejection of unearned raw-publication claims, deterministic manifest generation and refusal to overwrite a different local candidate. Twenty-three focused tests pass. This is a source-discovery catalogue; endpoint assessment, rights/pacing review, the request/object metadata index and raw storage are not completed by it.

The main health track legitimately appended observations while PR #244 was open. Correction e92845b protects the recorded original ledger prefix while validating new entries. It does not weaken historical byte integrity, rewrite earlier evidence or freeze ongoing work. Latest-main baseline validation passed 1498 tests, 95.95% coverage. Corrected hosted baseline checks remain pending. Full integrated catalogue validation is being recorded separately.

## Raw-retention and publication-evidence checkpoint

Baseline PR #244 merged after exact-head green checks. Capture 33305989413 succeeded but downloaded artifact 9730497676 lacked the original capture directories. NZ monitor 322525555 is disabled_manually. Donor #404 adds raw-file/WARC verification and fresh artifact restore before credit (917 tests, 93.39% coverage locally); hosted proof remains pending. HF summary dry run 33306106031 passed without a public upload. Receiver #247 prevents fabricated publication receipts (1499 tests, 95.94% coverage locally). Country completeness, durable public storage and takeover remain unverified. See operational-followup-20260830.json and publication-guard-validation.json.

## WARC container and late failure handling

PRs archive-govt-nz#246/#247 and fyi-archive#404/#406 are merged. Follow-up capture 33307488567 failed before credit because the pinned adapter writes multiple WARC records within one gzip member. No artifact survived that failure; exact recovery 33307589477 cleared only its lease and preserved credited offset 17226. Donor #407 adds bounded whole-container parsing and moves failure retention/release after verification. Local validation passes 921 donor tests (one skip, 93.40%) and 1522 receiver tests (95.98%). Hosted restoration remains pending. No matching local Codex automation configuration referenced either repository; GitHub NZ monitor remains disabled. Details: container-recovery-20260830.json.

## Bounded original-byte restore passed

Donor #407 merged at be992fe036d5a270e228b5277e5b5770b9950ad8 after exact-head green checks; merged tree matches the tested branch. One-request run 33307777685 passed capture, raw verification, upload, clean download and verification before credit. Local independent download verified all seven inventory files (49,405 bytes, two WARC responses); its raw manifest hash matches both batch evidence and the issue receipt. This sample had no attachments; compressed attachment preservation is tested locally, not newly established by this live sample. Installed fyi-cli is 1.2.1.

Queue credit is now 17227/33208, leaving 15981 unprocessed entries and zero active leases. The 41,602-byte artifact expires on 2026-11-28; temporary retention is not durable HF storage. Monitoring remains disabled until source eligibility, durable retention and historical raw gaps are reconciled. No additional public HF upload, country-completion claim or cutover occurred. Receipt: hosted-raw-restore-20260830.json. All phase-level acceptance gates remain as listed in plan.md.

## Local package self-review — 2026-08-31

Reviewed path/member traversal and symlinks, outer gzip expansion limits, preservation of compressed HTTP payloads without double decoding, exact inventory and WARC correspondence, original versus normalized JSON, content-addressed deduplication, JSONL/Parquet agreement, source/event identity, tampered and interrupted restoration, and sanitized command failures. Adversarial tests and four killed integrity mutants support the local preservation contract. No country completeness, source rights, public publication or operational cutover is inferred.

Outstanding finding: the source adapter silently omits attachment HTTP 404 responses. Current indexes describe observed resources only. Attachment discovery/gap accounting and public delivery remain required follow-up work; the NZ monitor stays paused.

Attachment self-review passed for local indexes and restoration. Reviewed unsafe references, discovery budgets, missing/ambiguous parents, false HTTP statuses, changed hashes, duplicate/omitted rows, deterministic regeneration and v1 compatibility. The public sample has no attachment links; adversarial fixtures establish gap behavior. No source completeness or publication claim follows.

## Verified publication self-review — 2026-08-31

Reviewed anonymous revision-pinned fresh downloads, immutable path and digest checks, conditional parent commits, restore before promotion, retry idempotency, public/gated identity, catalogue child visibility, exact raw source/manifest/rights/privacy decisions, attachment gaps, sanitized failures and receipt creation races. The 137 focused tests pass with 100 percent measured critical-module coverage; four integrity mutants are killed. A real public metadata snapshot passed anonymous byte verification. Local full-suite timing failures remain explicit; hosted assurance is pending. Dataset viewer behavior is not yet verified. Raw rights/privacy clearance, public raw restore and cutover remain open.

Directory overlay review: verified saved source hash, explicit country mappings, every source host, path/symlink rejection, ambiguous/missing mappings and unobserved new sources. Twenty directory tests pass with complete branch coverage. Directory absence is never interpreted as national absence; no source adapter or rights status is promoted.

The first hosted metadata run exposed an insufficient idempotency fixture: the
previous retry case had no table configurations. The real catalogue now runs twice
in regression coverage and must retain the same revision with no new commit.
Card order is generated from one fixed table registry, retaining compatibility
with already-published cards. Failure reason output is an explicit allowlist;
unknown/private exception text remains unclassified and is never printed.

Hosted correction review: the receiver repeated the same public metadata verification successfully and preserved the exact revision, without snapshot/card rewrites. The first failure and its artifact remain recorded. Metadata authentication and public readback are proven; raw write capacity and public raw restoration are not. All country-completion counts remain zero and the donor monitor stays paused.

## Durable control continuation review — 2026-08-31

Three parallel review streams covered scheduling, owner/parity checks and durable
state, followed by cross-review of the integration. Findings included truncated
SQLite history, allocation before byte limits, permissive numeric/evidence types,
canonical-origin aliases, owner identity types, dimension allocation before
bounds, omitted retired lease tokens and incomplete verified-job identifiers.
Corrections require regression coverage before acceptance. These checks validate
structure and local transactions; they do not authenticate source rights or
externally supplied capture/publication receipts.

The owner and queue share a single local CAS document. A transition callback must
be pure; side effects before the CAS could not be undone by a conflict. A local
pre-action fence check is not a distributed guarantee. Hosted publication must
reject stale generations atomically at its sink, or execution and transfers must
be serialized by one authority. No deployment or cutover follows from this slice.

Source evidence improves the Canadian nil-return candidate assessment without
substituting a machine screen for an accountable privacy decision. Sample bytes
are preserved outside temporary worktrees with restricted filesystem permissions;
they remain on one physical disk and are not independently replicated or public.

## Shared execution continuation review — 2026-08-31

- Global queue admission must use one pinned authority snapshot and exact-parent
  non-forced Git ref updates; backend tests and four mutation probes cover stale
  writers, global pins and public-field restrictions. Privileged ref reset remains
  outside this application guarantee and is documented.
- Local capture completion is distinct from public credit. `record_capture`
  requires an exact live job lease and verified local manifest; its terminal state
  clears resource reservations, retains lease history, and forbids a public
  revision. Focused critical coverage is 100%; seven local control mutants fail.
- Independent review caught an unchecked CKAN success envelope. The adapter now
  requires literal true and rejects truthy substitutes, failed responses and
  malformed rows. Source metadata remains private; its licence field alone is
  not an authenticated acquisition or privacy decision.
- Bounded input did not by itself bound generated indexes. Added row, index and
  package ceilings before writes, including the separate restore copy. No rows
  are silently dropped to satisfy a ceiling.
- Source and country denominators remain unknown. CA nil-return rows and US XML
  text-element counts are explicitly different units, not comparable request
  totals or country completion. US narrative/case-title fields remain private.
- Grouped standing-policy options are proposed only. The CA candidate policy
  excludes raw provider contact metadata and preserves original/derived identity;
  future drift or sensitivity findings reopen review. No user identity or rights
  approval was fabricated.
- Full repository and hosted deployment evidence remain pending at this review
  checkpoint; no cutover, public raw upload or complete-system claim is made.
