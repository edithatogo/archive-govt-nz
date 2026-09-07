# Profile-bound Budget selection drift

Phase 3.3 bounded increment for M-05/M-07/M-18 and S-04; AC-03/AC-05/AC-16.
Base `b70ddf75594da985f01938cf4724be7e019a416d`, isolated branch
`codex/health-layout-drift-20260907`. Parent owns shared lifecycle files and
full integration assurance; Popper owns the donor-SQLite library boundary.

## Contract and scope

`layout_drift.compare_budget_layout(reference, reference_sha256, observation,
observation_sha256, *, profile)` accepts two explicitly pinned local Budget
packages. Supported profiles are `budget-2025/v1` and `budget-2026/v1`; both
inputs must declare the same selected vintage. It composes the existing bounded
`read_verified_budget` contract, including package fixity, exact table shapes,
row dispositions, numeric consistency and field/column lineage bijection.
It uses the existing schema serialization SHA-256 convention, not a new schema
registry. No extractor, normalizer, schema, pipeline or publication path changes.

The deterministic receipt binds profile/transformation, both manifest pins,
original-object identities as recorded in those manifests, all derivative hashes,
counts, column positions and output-schema hashes. The selected-sheet signature
includes the fixed sheet/header/first-data-row, Vote-Health filter, ordered column
positions, SHA-256 of each header label and known target roles. Unknown extra
labels are hashed, not copied into evidence. Unselected sheets and complete
workbook-area coverage are outside this signature.

Changed values, observation/package identity or row counts do not themselves
change column selection. Reordered columns or renamed extra headers produce
`selection_drift` and `reference_selection_matches: false`; both signatures
remain available for review. This is deliberately stricter drift observation
than the named-column extractor, which can safely handle reordered columns.
It does not declare such packages corrupt or silently choose a new profile.
Unknown profiles, cross-vintage comparisons and invalid packages raise the
redacted `budget_layout_contract` error, never a matching receipt.

The reference is caller-designated, not a registered/approved source-layout
baseline. A matching receipt grants no normalization, mapping, rights or
publication approval. Positions come from validated retained lineage; originals
are not reopened, headers are not independently re-observed in XLSX, and source
authenticity is not proven. The inherited reader's observation-ID preimage
limitation and bounded-Parquet parsing limitations remain explicit. Existing
input schemas are required; unsupported schemas fail rather than being promoted.
This does not complete the broad adapter-interface, dimensions, data-area
normalization, or Phase 3 tasks.

## Validation and failure record

The first test collection failed because the new module did not exist (red,
exit 2). Implementation passed the initial 13 tests. An additional independently
constructed expected selection assertion binds every column and input hash and
checks caller Decimal-context independence. Final results: 14 dedicated cases,
77 combined tests with the existing Budget reader; new module 41/41 statements
and 6/6 branches (100%). Cold unfiltered mutation: 11 killed, zero survivors,
zero cache hits, 11 misses; 14 tests, 2.95 seconds. The inherited runner selected
10 workers. One module-not-measured warning occurred in the no-cov mutation
invocation; separate critical coverage passed. No exclusions or thresholds changed.

Initial lint found formatting/import/raw-regex issues; initial typing found an
optional dictionary lookup. These were fixed, with final Ruff lint/format and
scoped BasedPyright passing. The first coverage invocation accidentally used
slashes in its module name: tests passed but no coverage was collected, exit 1.
The corrected dotted module target measured 100%; the failed setup is not a
coverage pass. The replay's initial candidate path referred to the older
`raw-budget-d26e769` package with a different manifest; read-only hash comparison
resolved the correct pinned orchestrated package before replay. The standalone
replay has only an implicit-package lint exemption; runtime checks remain active
under optimized Python. No full harness, remote mutation or lifecycle edit occurred.

## Actual retained replay

`replay.py` reads existing packages without extracting workbooks or writing
outputs. `retained-replay.json` is its deterministic local stdout capture.
Each package was self-compared twice, and all four package files were rehashed
before and after. The final recipe rerun matched the retained receipt byte-for-byte.

| Profile | Retained package | Normalized rows | Manifest SHA-256 |
| --- | --- | ---: | --- |
| Budget 2025 | `raw-orchestrated-20260830-v1/budget` | 215 | `1b1e5dfd3fa90d98dcf5200997001db236df7b40f4404b658c36f5cb0264d2fe` |
| Budget 2026 | `raw-budget-2026-20260831-v1` | 185 | `f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738` |

Both yielded column signature
`11584d38b79fa4b6e2b828b8eded9367fe7f0ea7352395a348479d821fbdc45f`.
This numerical signature equality does not establish cross-vintage comparability;
the API rejects cross-profile input. Real evidence is same-package repeatability,
not observation of a newly captured revision. Drift scenarios use synthetic tests.

## Reproduce

Use the repository's locked interpreter with this worktree's `PYTHONPATH=src`.
Commands below omit the local interpreter prefix for portability.

```sh
python -m pytest -q tests/domains/health_appropriations/test_layout_drift.py tests/domains/health_appropriations/test_budget_reader.py --cov=archive_govt_nz.domains.health_appropriations.layout_drift --cov-branch --cov-report=term-missing --cov-fail-under=100
python -m pytest -q tests/domains/health_appropriations/test_layout_drift.py --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/layout_drift.py --gremlin-report=console --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov
python conductor/tracks/health_appropriations_medallion_assimilation_20260829/layout-drift-20260907/replay.py /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver
```

Self-review checked profile isolation, deterministic identity, complete selected
column accounting, raw-label minimization, inherited source bounds, refusal of
schema/pin/lineage tampering, and nonmutation. Conductor implementation guidance
informed requirement binding and retained failures; the user's scoped delegation
overrode shared lifecycle edits/full-harness steps. Parent independent review
and coherent full assurance remain required before integration acceptance.
