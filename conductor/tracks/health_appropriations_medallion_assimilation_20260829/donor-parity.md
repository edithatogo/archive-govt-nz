# Phase 4.1 donor row oracle — 2026-09-07

Scope: M-08/M-18; AC-06/AC-11/AC-16. Isolated from base
`438d918a23d6da303fd6ea5767b3ec151f493b90` on
`codex/health-donor-parity-20260907`. Parent owns lifecycle and full integration
validation. No plan, metadata, runlog, registry or existing module was changed.

## Audit and implementation

Existing `donor.py` preserves the complete snapshot; `silver.py` retains donor
row numbers and raw values; `gold.py` regenerates five fixed SQLite schemas.
Budget/forecast adapters, `raw_compatibility.py`, `compatibility_export.py` and
`historical_reconciliation.py` already implement source extraction, exact-value
sidecars and the historical source/donor union. They were reused, not duplicated.
The gap was a reusable all-table row oracle and explicit per-occurrence ledger.

`donor_parity.py` reads at most 16 MiB into an in-memory query-only database,
verifies the supplied SHA-256 before parsing, checks integrity and the existing
five-table/column schema, and caps total rows at 10,000 and SQLite VM work.
SQLite never opens the original path, writes journals, or executes donor code.
This is bounded parsing, not a hostile-process sandbox or a concurrent-filesystem
immutability claim. WAL-dependent databases are not supported.

Each row digest includes cell types, exact float hex tokens, nulls and all text.
Matching is a multiset operation retaining duplicate multiplicity. Insertion
order is not semantic equality; donor and candidate row ordinals remain in the
receipt. A replacement records both donor-only and candidate-only occurrences,
without guessing a business key or tolerating numeric differences. Mismatch IDs
bind both input hashes, table, ordinals and row content. Counts matching the
312-row baseline are a separate explicit flag, not inferred from equality.

The frozen `Repair` dataclass is the executable repair-ledger schema: each
entry requires the exact mismatch ID, source object SHA-256, source coordinate,
rationale and executable test reference. Duplicate, stale and unused entries
fail closed. A supplied explanation is neither a test execution attestation nor
accountable repair approval. The receipt explicitly says `not_asserted`.

## Observed actual retained bytes

`donor-parity-replay.py` replays the fixed retained packages read-only.
`donor-parity-observed-20260907.json` contains row digests, ordinals and source
coordinates; it contains no original SQLite values or source payloads.
Two independent invocations produced byte-identical evidence, SHA-256
`03ec9f8818b8bdb0a2170cedb6e789f0cb26a0c80f21679751b48bb1e7424d49`.

The pinned donor manifest is
`893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74`.
All 23 CAS objects / 6,604,301 bytes verified, including donor database
`a2f9973846e1213823b499e4a019d314485110e80e4ee5a8984ebf3f35c85c8e`.
The recipe verifies 29 input files before and after comparison. It verifies the
retained manifest and CAS, not a fresh Git archive reconstruction or capture.

| Table | Donor | Donor-derived Gold matches | Source-derived matches / added |
| --- | ---: | ---: | ---: |
| GDP historical | 53 | 53 | 53 / 0 |
| BEFU summary | 10 | 10 | 10 / 0 |
| HYEFU summary | 10 | 10 | 10 / 0 |
| Historical Health | 24 | 24 | 24 / 29 |
| Recent appropriations | 215 | 215 | 215 / 0 |

The donor-derived Gold database has exact 312-row parity. The source-derived
341-row database retains all 312 donor rows and restores 29 annotated historical
years, each joined to the existing historical reconciliation and source cell.
Recomputing the exact historical comparison yields 76 exact matches, 29
source-only rows and one exact-decimal difference. All 30 deviations retain
source identities/coordinates, reason, rationale and a regression-test link.
The 15 REAL binary-representation flags are distinct from those 30 deviations.
SQLite equality does not erase the exact-decimal discrepancy. Both derivatives
and all source bytes remain unchanged outside Git.

## Validation and self-review

Use the locked repository environment; in this run the existing main-worktree
interpreter was used with `PYTHONPATH=src` so imports resolve to this worktree.
No dependency installation or environment mutation was required.

```sh
export PYTHONPATH=src
python -m pytest tests/domains/health_appropriations/test_donor_parity.py \
  tests/domains/health_appropriations/test_donor.py \
  tests/domains/health_appropriations/test_silver.py \
  tests/domains/health_appropriations/test_historical_reconciliation.py \
  tests/domains/health_appropriations/test_raw_compatibility.py \
  tests/domains/health_appropriations/test_compatibility_export.py \
  --cov=archive_govt_nz.domains.health_appropriations.donor_parity \
  --cov-branch --cov-report=term-missing --cov-fail-under=100 -q
python -m pytest --gremlins \
  --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/donor_parity.py \
  --gremlin-report=console --no-cov -q \
  tests/domains/health_appropriations/test_donor_parity.py
python conductor/tracks/health_appropriations_medallion_assimilation_20260829/donor-parity-replay.py \
  /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations
```

Observed red: missing module collection failure before implementation. Green:
115 focused/integration tests; oracle 118 statements and 38 branches, 100%
coverage. Seven existing SQLite ResourceWarnings arose in adjacent legacy tests.
The new 21-test suite includes generated multiset invariants, schema/value/null/
blob/duplicate/deletion fault cases, input limits, integrity and repair failures.
Mutation: 33 killed, zero survivors, zero cache hits. The first mutation run
failed because a test patched shared SQLite; review fixed the module binding
instead, preserving coverage's independent SQLite use. The successful run emitted
one coverage module-not-measured warning, not a mutation failure.

Ruff lint/format and strict Pyright cover the new module, tests and replay recipe.
Self-review checked exact hashes, schema closure, duplicate accounting, original
nonmutation, redacted evidence, stale repairs, source-cell joins and scope.
The standalone replay keeps linear audit code with local complexity/namespace
lint exemptions; the production module has no such exemptions.

## Exact remaining clauses

- Phase 4.1's row-oracle/repair-schema implementation and bounded real execution
  are evidenced here. The parent must reconcile lifecycle status and run the
  current full harness; no phase or track completion is asserted.
- AC-06's accountable approval of intentional semantic repairs is not asserted.
  The unchanged 312-row donor-derived product needs no value repair. The raw
  product's explanations preserve both observations and do not promote it.
- Phase 4.1's other clause (complete extraction fixtures across all workbook
  areas/failure families), Phase 4.2 complete in-scope normalization, and Phase
  4.4 combined 23-file/four-analysis/six-plot clean reconstruction remain outside
  this slice. Existing capability does not establish their full acceptance.
- AC-11 broader cross-source quality/classification drift and AC-16 full
  repository/hosted assurance remain parent work. No new rights decision,
  acquisition, publication, remote mutation or donor retirement occurred.
