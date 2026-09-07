# Canonical factual source index — 2026-09-07

P2.16 joins the retained rollout and dated assessments into one schema-versioned
metadata catalogue: **255 sources, 251 entities (250 geographic plus EU), 42
regimes, 30 original sources preserved exactly, 225 factual candidate assessments**.
The original 23 runtime / 29 site seed provenance remains unchanged.

This is repository-local generation, not publication, activation, fresh access,
raw reconstruction, or exhaustive national/world discovery. The parent owns full
integration, hosted validation and P2.2/P2.3 lifecycle acceptance.

## Delivered interface and artefacts

- `archive_govt_nz.foi_canonical.build_canonical_catalogue(seeds, track)` returns
  the joined v2 registry.
- `build_source_index(seeds, track)` uses the existing catalogue exporter to
  generate the complete registry, sources/entities/jurisdictions JSONL, machine
  coverage, human coverage, original rollout-state projection, AL navigation
  assessment and manifest. No network or filesystem write is performed by either
  function.
- [Input pins](canonical-inputs-20260907.json) identify all fourteen fixed inputs.
  Existing source receipts are checked through the reconciler and compared with
  the pinned lineage report, including the legitimate 27 missing *seed* receipts.
  Missing candidate receipts fail; seed missing-receipt markers are not fabricated.
- [Registry](canonical-index-20260907/registry.json),
  [human index](canonical-index-20260907/coverage.md),
  [machine coverage](canonical-index-20260907/coverage.json),
  [manifest](canonical-index-20260907/manifest.json), and
  [v2 schema](canonical-source-catalogue-v2.schema.json).

The existing scheduled/publishing entrypoint stays on its previous v1 path.
This delivery supplies an explicit canonical build API and its generated index;
it does not silently change any hosted job, publisher or schedule.

## Meaning of the joined dispositions

Every entity links its exact source set and source-specific dispositions. All
225 candidates retain factual review, access, FOI scope, attribution uncertainty,
rights, privacy, schedule/publication flags and null request denominators.
Original 30 source rows remain object-equal to the pinned catalogue, including HF
identities and existing review-required labels. Their entity dispositions cite
seed/directory evidence rather than claiming new access or rights review.

The six guarded linked findings remain endpoint-specific overlays: AL register
table/landing and JM/KY information interfaces were observed; GG timed out and UM
was blocked by unsupported robots rules. The earlier UM observation is retained
in historical evidence, not represented as current guarded success.
AL's separate year-index assessment retains ten links spanning eleven years,
unknown linked media types and an unverified capture adapter; no link is followed.

Parent-source access and linked-endpoint access are separate dated observations,
not one aggregate latest-success flag. Pacing metadata retains absent policy as
null; it does not certify historical compliance or authorize future requests.
The pre-fix correction and guarded acquisition provenance are pinned inputs.

The entire historical rollout state (including raw counters, denominators,
receipt paths, execution flags and outstanding work) is copied unchanged into a
separate projection. No table/attachment-link count becomes a request denominator.
Coverage still has total_requests=null, verified_complete=0 and no payload
publication authority. Unknown/restricted dispositions cannot grant execution;
restricted/disallowed candidate gap rows omit endpoint URLs.

## Local acceptance and review

The exact canonical-join gap identified after P2.15 is now implemented. Under
P2.2/P2.3, blocked/unknown evidence-backed dispositions and null denominators are
valid outcomes; inaccessible sources do not create a human factual-review queue.
This does not satisfy R04 external catalogue publication or R07 raw delivery.
No umbrella status, metadata, global registry, parent accepted P2.5–P2.8 status,
or frozen worktree was changed.

Conductor implement/review guided the provenance checks, explicit failure
semantics, unchanged-policy assertions and synthetic negative joins. No new
platform dependency or rights decision was introduced.

- 330 focused tests passed in the final run.
- Both changed production modules: 100% line and branch coverage.
- Seven in-memory guard mutants killed: duplicate identities, candidate-set
  equality, receipt/entity association, receipt digest, input digest, execution
  promotion and recomputed assessment mismatch.
- Positive/negative v2 schema validation; actual byte-for-byte reproduction of
  every generated artefact and its manifest hashes; unchanged 30 source rows;
  candidate ordering independence and synthetic two-entity raw-counter preservation.
- Scoped Ruff format/lint and BasedPyright passed. No full harness was run.

Initial red test failed because the canonical importer did not exist. During
development, an early failed probe lacking robots_policy was corrected to retain
null, and the input-drift regression was tightened to demand the correct guard's
error. An initial combined coverage run omitted the existing seed-symlink test
module (322 tests passed, coverage gate failed at 97.87%); adding that relevant
module and the final ordering regression produced the reported 330/100% result.
These are test/development findings, not new source observations.

## Reproduction

From the isolated worktree root, with its `src` first on PYTHONPATH:

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest \
  tests/test_foi_canonical.py tests/test_foi_canonical_mutants.py \
  tests/test_foi_year_navigation.py tests/test_foi_linked_assessment.py \
  tests/test_foi_candidate_probe.py tests/test_foi_candidate_cohort.py \
  tests/test_foi_candidate_assessment.py tests/test_foi_reconciliation.py \
  tests/test_foi_catalogue.py tests/test_foi_discovery.py tests/test_foi_rollout.py \
  tests/test_verify_foi_rollout_evidence.py tests/test_foi_seed_provenance.py \
  -q --cov=archive_govt_nz.foi_canonical --cov=archive_govt_nz.foi_catalogue \
  --cov-branch --cov-report=term-missing --cov-fail-under=100
```

`test_actual_index_reproduction` reconstructs the index without network or writes
and compares every committed byte; mutation subprocesses have 30-second limits.
The v1 exporter remains covered by the adjacent original tests.

Next action: parent review and full integration gate for this coherent commit,
then parent lifecycle acceptance. No new external evidence or human factual
approval is needed to complete this local join.
