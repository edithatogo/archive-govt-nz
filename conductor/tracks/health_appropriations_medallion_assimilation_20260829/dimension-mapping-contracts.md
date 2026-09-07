# Pure dimension/mapping contracts — 2026-09-07

Local additive slice from `d69b94c5d9e7ae3083c2fc24f66d814817429a90`.
Implements part of Phase 3.2, M-06 / AC-05 / AC-11. This does not complete
that clause, establish factual mappings, or authorize publication.

## Contract and trust boundary

`dimension_mapping.py` accepts immutable typed caller assertions. Ten supported
kinds are vote, appropriation, department, portfolio, amount type, functional
classification, economic classification, measure, unit and period. Literal
scheme (caller must include the scheme version), label, kind, inclusive start/end
dates and optional original period token form a deterministic SHA-256 key.
No case folding, alias resolution, unit conversion or fiscal-year inference occurs.
Null endpoints represent uncertainty and overlap conservatively, not proof of
unbounded source validity. Different labels/schemes are not equated.

Each snapshot permits one assertion per dimension key, with explicit vintage and
mapping-contract version. Null target is unresolved and cannot carry a method or
mapping evidence. A nonnull target requires a nonblank method and sorted, unique
SHA-256 evidence references. These references are **not read or authenticated**;
acceptance is structural assertion validation, never approval or factual truth.
No real mappings are supplied by this change.

Overlapping periods for the same kind/scheme/literal label must agree on target,
vintage and mapping version. Unknown versus mapped conflicts too. Adjacent periods
sharing an endpoint overlap; a subsequent day does not. No precedence is inferred.
Comparison validates both snapshots and reports additions, removals, and changes
to vintage, version, target, method or evidence. Period/label changes are separate
removed/added keys, not guessed continuations. Mapping confidence is not modeled.

Bounds: 1,000 assertions per snapshot, 4,096 characters per text field, 32 evidence
digests per assertion; at most 499,500 pair checks. Inputs are tuples rather than
unbounded iterables. No filesystem/network I/O occurs in production.

The optional canonical classification bridge reuses `validate_table` and accepts
only the existing unmapped Budget occurrence scheme. It provides a pooled literal
dimension view without mutating or replacing source occurrences or their lineage.
The caller must retain that original table; this view is not a lineage package or
an authoritative conformed classification. It does not invent a scheme version.

## Tests and review

Initial three tests failed at collection with `ModuleNotFoundError` before module
creation, then passed. Expanded synthetic suite: **50 tests**. Existing Budget
projection is exercised through a synthetic workbook; no retained or live source
bytes are used. Properties check input-order independence. Negatives cover malformed
types, all ten kinds, identity components, exact bounds, dates, duplicate keys,
unresolved assertions, evidence, overlapping conflicts, revisions, drift and bridge
scope. Input tables remain unchanged.

Final affected run: **443 passed**, 100% coverage of the new module's 106 statements
and 28 branches. Dedicated cold mutation runner: baseline exit 0, **21/21 killed**
with pytest exit 1 (collection errors do not count). First run had two survivors
for evidence digest/bounds: other unresolved-state checks masked them. Added
independent mapped-state negatives; final cold rerun killed both. No production
guard was weakened. Runner copies source into temporary directories; it never
mutates this worktree or calls a source endpoint.

Ruff format/check, focused basedpyright with the existing Python environment,
and `git diff --check` pass. The first unconfigured pyright attempt could not
resolve the sibling runtime; final basedpyright explicitly selected it. Tests use
casts only for deliberately invalid runtime inputs.

Self-review found no remaining in-scope blocking issue. No adapters, canonical
schemas, dependencies, shared plan/runlog/metadata or existing evidence changed.
No full harness, hosted checks, source capture, rights promotion or publication.
Parent owns integration and full-gate evidence; frozen delivery remains untouched.

## Reproduction

From this worktree, use the existing locked environment's Python and binaries
(during review: `/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/`).
Set `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`; use a fresh temporary directory
for `COVERAGE_FILE` and `HYPOTHESIS_STORAGE_DIRECTORY`.

```sh
python -B -m pytest -q -p no:cacheprovider \
  --cov=archive_govt_nz.domains.health_appropriations.dimension_mapping \
  --cov-branch --cov-report=term-missing \
  tests/domains/health_appropriations/test_dimension_mapping.py \
  tests/domains/health_appropriations/test_budget_classification.py \
  tests/domains/health_appropriations/test_budget_projection.py \
  tests/domains/health_appropriations/test_historical_projection.py \
  tests/schemas/test_health_recordsets.py \
  tests/schemas/test_health_recordset_json.py \
  tests/schemas/test_health_recordset_normalization.py
python -B tests/domains/health_appropriations/dimension_mapping_mutations.py
```

Run `ruff format --check`, `ruff check`, and
`basedpyright --pythonpath <existing-environment-python>` on the three Python
paths pinned in the paired JSON evidence. No new environment/dependency is needed.

## Exact remaining scope

- Source-backed stable identifiers/crosswalks for each actual dimension family;
  this slice provides a validator, not a populated authoritative registry.
- Evidence-byte/coordinate binding, mapping confidence policy and adjudication.
- Source-effective periods, cross-vintage continuity and classification-drift
  thresholds supported by actual sources, not synthetic equality checks alone.
- Broader source projections, unit/period equivalence, fact-to-dimension linkage,
  conformed Gold contracts and Phase 7 federation.
- Parent integration, full harness, hosted delivery and lifecycle reconciliation.

Popper's SQLite work and Meitner's source/layout-drift work are unchanged.
