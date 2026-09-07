# Canonical disposition validation — 2026-09-07

Isolated from G `70cd15b0876a87112d8eea65626858a65eb62acd` on
`codex/foi-disposition-validation-20260907`. This is a local implementation
receipt, not phase closure or an AC04 acceptance decision.

`foi_disposition_validation.validate_canonical_dispositions(seeds, track)`
reuses `build_source_index` to verify all canonical input pins, seed provenance,
retained receipts, assessment replay and exact joins before reporting success.
It accepts neither caller-provided catalogues nor success flags. The receipt
has scope `catalogue_disposition_validation`, explicit seed/canonical input pins,
a digest of the complete builder provenance, unchanged
coverage and SHA-256/size pins for every generated file, including the manifest.
There is no `phase_acceptance` field. Exhaustive discovery, capture, publication,
programme completion and parent AC04 audit remain separately unevidenced gates.

Unknown FOI scope, inaccessible sources and unsupported robots are valid bounded
dispositions, not discovery exhaustion or capture proof. All 255 source rows,
251 entity dispositions, null denominators, historical raw state, rights and
schedule fields remain unchanged in the canonical outputs. The underlying
legacy validator is unchanged, including its stricter legacy blocked result.

The optional CLI selector invokes this separate function. Without the selector,
the old function, output shape and exit status remain unchanged. Explicit
canonical file output uses exclusive creation; an existing receipt is preserved.
Invalid inputs produce an exception/nonzero exit before any output receipt.
Stdout-only validation performs no output-file write. No publisher is invoked.

## Reproduction

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python tools/validate_foi_catalogue_phase.py --canonical-track conductor/tracks/global_foi_public_archive_20260830
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/test_foi_disposition_validation.py tests/test_foi_disposition_mutants.py tests/test_foi_phase_validation.py tests/test_foi_canonical.py tests/test_foi_canonical_mutants.py -q --cov=archive_govt_nz.foi_disposition_validation --cov=tools.validate_foi_catalogue_phase --cov-report=term-missing
```

The paired JSON is the actual stdout receipt from the first command, not a
manually assembled acceptance flag. Offline tests independently compare the
regenerated file bytes against the retained canonical index.

## TDD and focused review

Final focused result: **100 passed**, including ten static mutant kills;
new validator and CLI each have 100% statement/branch coverage. Ruff format/lint,
BasedPyright and track-local integrity checks passed. Actual offline receipt:
[canonical-disposition-validation-20260907.json](canonical-disposition-validation-20260907.json).
The receipt avoids duplicating the directory review: full provenance is
digest-bound and explicit seed/input pins remain readable. Its actual serialized
size is tested below 20,000 bytes; no generic arbitrary-input memory claim is made.

Initial red: missing function module, followed by unrecognized CLI option.
Faults include every one of the fourteen canonical input pins, a seed pin,
missing receipt, rehashed forged disposition, duplicate source, cross-entity
source and publication promotion. Existing canonical tests also exercise exact
join/receipt failures and raw-count preservation. Three new static mutants
replace replay with cached files, corrupt output digests and promote programme
completion; seven existing canonical guard mutants cover underlying joins and
receipt/replay validation. Socket connections are denied in new API tests.

The missing-receipt test was corrected to expect the actual `rollout_integrity`
failure. CLI coverage initially omitted the aliased/relative entrypoint; using
the normal import and absolute script path measured the exercised code without
exclusions or lowered thresholds.

Conductor implement/review guided the compatibility and authority audit. No
tracked inputs, historical observations, legacy validator, plan checkboxes,
metadata, global registry, rights decisions, schedules or publication changed.
Parent owns AC04 audit, integrated full checks and lifecycle acceptance.
