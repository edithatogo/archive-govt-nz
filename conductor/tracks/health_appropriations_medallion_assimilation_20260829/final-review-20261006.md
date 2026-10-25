# Health Appropriations final review — 2026-10-06

## Decision

Phase 9 reconstruction and final local review are evidenced for the products
currently supported by the repository. The Health Appropriations track remains
open and is not certified complete: 31 plan tasks remain unchecked or partial,
including Must-level work in Phases 1–8 and the final completion gate. The
external publication and collection receipts remain valid historical evidence;
this review performed no publication or collection mutation.

## Automated evidence

- `uv run --locked python tools/health_recovery_assurance.py --receipt conductor/tracks/health_appropriations_medallion_assimilation_20260829/clean-room-recovery-20261006-final.json`
  completed successfully. It rebuilt 22 currently wired product lanes from
  pinned Bronze inputs in a disposable derivative root, compared paired
  outputs, and confirmed `bronze_objects_unchanged: true`. The receipt reports
  `partial_with_blockers`, explicitly leaving cross-source comparison,
  remaining source-native Silver profiles/canonical adapters, and complete
  DCAT/Croissant/RO-Crate/PROV Platinum profiles unreconstructed.
- `uv run --locked python tools/validate_health_source_census.py conductor/tracks/health_appropriations_medallion_assimilation_20260829/source-census.json`
  passed for 143 resource records across 13 families. The rebuilt source-health
  report is `verified_repeat_identical`: 75 captured and 68 out-of-scope
  resources. Eleven contextual series remain unqualified and their rights
  remain `not_evaluated`.
- `uv run --locked python tools/check_claim_drift.py --output /tmp/health-claim-drift-20261006.json`
  passed with zero divergences. `uv run --locked python
  tools/validate_conductor_state.py` passed with zero errors across 93 tracks.
- `./scripts/validate.sh` passed after the review register and plan update: 7,490
  tests passed, 10 skipped, 97.77% coverage against the unchanged 80% floor;
  formatting, lint, typing, 56 schemas/46 representative documents, 9/9
  parity cases, configured mutation gates, dependency/licence/secret checks,
  and 113-component SBOM validation passed on the documented tree.
- Live GitHub reconciliation: PR #647 is merged at `f43bea497dfbdb5f51f57b81355b506176084bf5`.
  The only open PRs are #539, #538, #537, #527, and #496; they are dependency or
  automation updates outside this track. Phase issues #209, #210, #211, #213,
  and #215 remain open and correspond to unfinished plan phases. No issue was
  closed based on partial recovery evidence.

## Findings and disposition

| Class | Finding | Disposition |
| --- | --- | --- |
| Code defect | No defect was exposed by the integrated recovery, claim-drift, Conductor-state, or source-census checks. | No code change indicated by this review. |
| Missing local implementation/evidence | Thirty-one plan tasks remain unchecked or partial. Recovery still lacks the cross-source comparison, remaining source-native profiles/adapters, complete Platinum profile set, and several broader Phase 1–8 products and operational contracts. | Keep the owning phase issues open; continue with bounded implementation slices. Do not mark the track complete. |
| Source/rights decision | The census has 11 contextual series unqualified and rights unevaluated. The Phase 4 donor ledger accepts all 30 historical differences as retain-both/no-replacement dispositions; this does not approve replacement values or publication. | Preserve original bytes and observed values. Keep comparability and redistribution eligibility unasserted until their separate evidence and rights decisions are complete. |
| External authority boundary | Prior candidate publication, hosted readback, and collection membership are already evidenced. | No external mutation was repeated. Any new publication or collection change remains a separate explicit approval gate. |

## Track reconciliation

The source/requirements/design/plan/evidence/recovery/publication claims were
compared against the current Conductor state and live issue/PR readback. The
recovery result supports only its enumerated product lanes; it does not prove
all Must requirements. Phase 9's review task is complete as a review, with
findings recorded and decision-dependent claims left open. The Phase 10.3
completion checkbox remains open until all Must requirements are evidenced.

## Addendum — 2018/19 Vote Health recovery lane

The bounded 2018/19 category-total profile added after the initial review is
now part of the integrated recovery path. The updated
`clean-room-recovery-20261006-vote-health-2018-19.json` receipt records two
identical Bronze-derived builds and unchanged Bronze objects, while retaining
the overall `partial_with_blockers` status and the previously classified
unresolved products and decisions. Focused tests and the full repository
validation harness passed on this exact tree. Review of the added integration
found no further local defect; the track and Phase 9 completion gate remain
open pending the documented work.

## Addendum — 2026-10-24 clean-room recovery and live claim readback

The integrated recovery was rerun from pinned Bronze objects in a fresh
isolated derivative root. `clean-room-recovery-20261024-final.json` records 47
product lanes, repeated outputs, `bronze_objects_unchanged: true`, and the
truthful status `partial_with_blockers`. The temporary derivative root was
removed after the run. Historical publication receipts were not changed and no
publication or collection mutation was performed. The expanded recovery now
includes rebuilt and repeated analytical metadata, canonical Gold, source-native
Silver, BIFF8 Budget/Revenue, and Vote Health supplementary products.

`claim-drift-20261024-final.json` records zero divergences across the five
archived-repository claims. The unauthenticated REST request had returned 404
for these private repository records. Read-only `gh api` readback confirmed all
five `archived: true`; `tools/check_claim_drift.py` now uses an explicit
`GH_TOKEN`/`GITHUB_TOKEN` when available and otherwise the existing GitHub CLI
credential, without printing or persisting the token. Focused checker tests
passed.

The independent source census validator passed for 143 records across 13
families. Conductor state validation passed across 93 tracks with zero errors.
The integrated receipt still explicitly leaves cross-source comparison,
remaining source-native Silver profiles/canonical adapters, and the complete
DCAT/Croissant/RO-Crate/PROV profile set unbuilt. Rights remain unevaluated.
The donor oracle still matches 312 in-scope rows across five tables. The
authoritative Phase 4 ledger accepts the 30 historical differences (29
source-only rows and one value difference) as retain-both/no-replacement;
replacement values remain null, with no repair or publication approval. This
disposes of the observed differences without claiming they reconcile to one
canonical value. Canonical Gold's own quality report continues to identify
source-health, revision-reconciliation, and cross-source reconciliation
reports as unresolved.

The track remains `partial_with_blockers` and is not complete. Phases 6–8 and
the final completion gate remain open. No completion checkbox or issue was
closed based on this recovery. The final harness outcome is recorded below; only
this textual evidence was appended after it passed.

The required `./scripts/validate.sh` run completed successfully on 2026-10-24
after all recovery, claim-readback, implementation, and test changes, and
before appending this textual result record. It passed lock consistency, Conductor state, formatting, Ruff lint, basedpyright (zero errors,
zero warnings, zero notes), all 8,366 collected tests (8,352 passed and 14
skipped), branch coverage at 97.10% against the 80% floor, 81 schemas and 71
representative documents, 9/9 parity cases, all configured mutation gates,
slop/hygiene, CAS throughput, dependency and licence audits, secret scanning,
and an 118-component SBOM validation. The SBOM tool emitted a non-fatal
CycloneDX validation-skipped warning before its successful SBOM validation
receipt. The test run emitted 18 warnings, including existing deprecation and
resource warnings.

The first full harness attempt ran while unrelated repository test jobs were
also consuming the host. It produced seven failures: one canonical-Gold fixture
lacked fresh MOH/Crown manifests, one Hypothesis case exceeded its 200 ms
runtime deadline, and five subprocess tests hit their 30-second limits. The
fixture was updated to include and assert all fresh manifests. All seven
failure-only reruns passed serially; the exact full harness then passed on the
updated tree. No test retry setting or global timeout was changed.

## Addendum — 2026-10-25 recovery refresh after BIFF8 Gold integration

Following the merge of PR #774, the preserved Phase 9 worktree was synchronized
with `origin/main`. Its clean-room receipt was regenerated against the compact
BIFF8 witness-report contract and current Gold verifier. The receipt records 47
rebuilt product groups, unchanged Bronze objects and no execution errors, while
retaining `partial_with_blockers`. The final gate still identifies
cross-source comparison, remaining source-native Silver profiles/canonical
adapters and complete DCAT/Croissant/RO-Crate/PROV Platinum profiles as not
rebuilt. Rights remain unevaluated; publication was not performed.

The retained CPI, QES, GDP and population package manifests remain bound by
their historical hashes. PyArrow 26 rebuild hashes are separately admitted
only after semantic row, schema and lineage verification. This separates
immutable retained evidence from new writer serialization pins.

The exact-tree `./scripts/validate.sh` passed on CPython 3.15.1: 8,420 passed,
14 skipped, 97.05% coverage, 81 schemas/71 representative documents, 9/9
differential parity, all configured mutation and supply-chain gates, and the
118-component SBOM. The track and Phase 9 completion gate remain open; this
recovery result closes no source, rights, implementation or final-completion
decision.
