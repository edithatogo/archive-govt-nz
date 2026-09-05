# Local FOI provenance and accounting review — 2026-09-06

Scope: P2.5–P2.7, AC04/AC09/AC11/AC12. This work is based on
`c5233ae7fc0beb065071cf3554596456f6575131` in the isolated branch
`codex/global-foi-safe-gaps-20260905`. No global registry, seed configuration,
legislation or health files are changed. No push, publication, source capture,
ownership transfer or third-party communication is part of this continuation.

## Reconciliation before implementation

- GitHub readback confirmed receiver PR #403 merged at
  `2026-09-05T12:57:35Z`, merge `463feb5476fc62c8fb0af01dbd65455e5e396dd3`.
  Git ancestry confirms that merge is included in the requested base.
- Native Conductor validation passed across 92 tracks with no errors.
- The pinned reviewed catalogue already contains 251 entities, 30 sources and
  42 regimes. Its phase verifier returns exit 2 with structural validation
  passed and acceptance blocked by broader discovery and country completion.
- The materialized rollout already contains 255 candidate sources across all
  251 entities, with no entity lacking a named candidate. Its reference/count
  verifier passes. These candidate entries are not additions to the pinned
  source catalogue and do not establish reviewed nationwide coverage.
- The local automation readiness verifier passes: metadata retains donor
  ownership, no cutover, the disabled NZ monitor observation, and receiver
  repository/main guards. This checks saved evidence and workflow text; it is
  not a fresh hosted cycle or live monitor-state observation.

## Concrete findings and fixes

1. P2.5: the importer hashed the files listed in provenance, then reread fixed
   filenames independently. Omitted, duplicate, substituted or swapped-role
   manifest entries could pass without binding every consumed document.
   Symlinks also passed. Seven red regressions reproduced these cases and a
   changed second read. The importer now requires the exact role-bound seed
   inventory, rejects symlinked inputs, and parses the bytes it hashed.
2. P2.6: phase validation omitted entity `known_sources` and
   `remaining_unverified` reconciliation, and Python numeric equality admitted
   booleans/floats as counts. Seven red regressions reproduced missing checks
   or the wrong failure classification. Exact integer counts and literal
   boolean completion flags now reconcile to source links and geography.
3. P2.7: a source could appear in a second entity's links while its correct
   owner still listed it; duplicate links also passed. An existing file outside
   the track could satisfy the evidence gate through traversal, an absolute
   path or a symlink. Five red regressions reproduced these cases. Validation
   now checks both link directions, duplicate links and resolved containment.

The changes tighten validation only. Seed catalogue bytes, country dispositions,
rights decisions, snapshot publication formats and acquisition state remain
unchanged. The rollout report adds `duplicate_entity_source_links`; invalid
paths use its existing `missing_evidence` failure channel.

## Validation commands

- `uv run --locked python tools/validate_conductor_state.py`
- `uv run --locked python tools/validate_foi_catalogue_phase.py`
- `uv run --locked python tools/verify_foi_rollout_evidence.py conductor/tracks/global_foi_public_archive_20260830/country-rollout-20260831.json conductor/tracks/global_foi_public_archive_20260830`
- `uv run --locked python tools/verify_foi_automation_readiness.py --track conductor/tracks/global_foi_public_archive_20260830 --workflow-dir .github/workflows`
- `uv run --locked pytest tests/test_foi_seed_provenance.py tests/test_foi_catalogue.py tests/test_foi_discovery.py tests/test_foi_phase_validation.py tests/test_foi_rollout.py --cov=archive_govt_nz.foi_catalogue --cov=archive_govt_nz.foi_phase_validation --cov-branch --cov-report=term-missing -q`
- `uv run --locked pytest tests/test_verify_foi_rollout_evidence.py --cov=archive_govt_nz.foi_rollout_evidence --cov-branch --cov-report=term-missing -q`
- `uv run --locked pytest tests/test_foi*.py tests/test_verify_foi_rollout_evidence.py tests/test_publish_foi_cli.py tests/tools/test_verify_foi_automation_readiness.py -q --no-cov`
- `PYTEST_XDIST_AUTO_NUM_WORKERS=2 ./scripts/validate.sh`

The first two coverage commands passed 71 and 9 tests respectively, with 100%
line and branch coverage for all three changed modules. Focused Ruff format,
Ruff lint and BasedPyright checks pass. Final broad results and commit IDs are
recorded in the paired JSON receipt and evidence ledger.

The final FOI suite passed all 483 tests. Seven isolated in-memory guard
mutations were killed by real pytest assertion failures (exit 1): seed
inventory, seed symlink, typed counts, remaining counts, entity counts,
rollout evidence existence and duplicate rollout links. Each mutation replaced
one uniquely matched guard in an imported module in a fresh Python subprocess;
no production source file was overwritten.

The full harness stopped at tests: 4810 passed, three failed, 97.62% overall
coverage. All three failures report Hypothesis timing instability against the
200 ms deadline in unchanged legislation/health tests:

- `tests/tools/test_legislation_parent_state.py::test_state_rejects_arbitrary_unrecognized_receipts`
- `tests/tools/test_merge_legislation_states.py::test_union_algebra`
- `tests/schemas/test_health_recordset_json.py::test_decimal_property_matches_arrow`

The run began before P2.7 review fixes were added; it is not certification of
the final tree. The final 483-test FOI run covers all three fixes. Global
format/lint, all six changed Python files' types, 48 schemas/38 representative
documents and the secret scan passed after the final source edits. The full
harness's later parity, mutation and supply-chain stages were not reached.
No failing test or deadline was changed, suppressed or excluded. P2.5–P2.7
remain in progress for the outstanding full/hosted gate even though their local
code and focused validation are complete and committed as requested.

One isolated diagnostic rerun of the three failing tests passed (3 tests,
3.14 seconds), without xdist or coverage. This supports the recorded timing
classification, not a replacement full-gate pass. Local commits are
`337e71d9` (P2.5), `455f7d4a` (P2.6) and `f5483f18` (P2.7).

## Review limits and remaining gates

The seed manifest remains the approved local trust anchor, not a cryptographic
signature proving third-party authenticity. Path checks are local metadata
integrity checks, not a defence against a concurrently hostile filesystem.
Rollout evidence existence does not authenticate its contents or confer capture
credit; phase accounting consumes reviewed flags and does not perform a restore.

No platform-guide manifest applies. General/Python style guidance is satisfied
through the repository's Ruff/BasedPyright workflow and existing module style.
No subagent execution tool was available; review is agent self-review.

P2.2–P2.4 and the whole track remain in progress. Broader source review and
reconciliation of the 255-candidate rollout into the pinned catalogue remain
open. Hosted recovery/parity, source-specific eligibility, public NZ and second
source acceptance, independent anonymous restore, eligible schedules and
receiver incremental-cycle evidence are still acceptance gates. This run does
not reverify older publication receipts or grant authority for any of them.
