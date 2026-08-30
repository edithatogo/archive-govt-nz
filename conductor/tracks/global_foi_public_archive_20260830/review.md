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
