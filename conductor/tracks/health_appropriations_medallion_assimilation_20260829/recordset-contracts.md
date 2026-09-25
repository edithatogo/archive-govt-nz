# Additive eight-record-set structural registry

The `schemas.health_recordsets` module provides an immutable, explicitly
versioned Arrow registry for the eight M-05 record sets. It does not replace
the existing domain schema, normalize a new source, migrate stored Parquet,
grant rights or alter publication metadata. The source-specific v1 tables
remain independently versioned and unchanged.

`recordset_schema(name, version="v1")` rejects unknown names and versions.
In particular, Ministry published indicators with unresolved units are not
silently assigned to `health_spending_fact`. Every shape carries source
identity, original schema/record pointers, vintage, observation context,
rights, quality flags, transformation and lineage slots. Unknown valid-time
endpoints and missing original observation IDs remain nullable; a required
status/context field allows subsequent validators to distinguish those cases.

The initial registry is structural; the later opt-in JSON/Arrow normalizer adds
typed row admission for constants, unique nonblank IDs, reason-coded nulls,
fixed-precision amounts and ordered valid-time endpoints. Source adapters add
source-specific identity derivation and linked lineage checks. These layers
still do not prove that an ID is factually correct, a classification is
equivalent, a unit or period is analytically compatible, rights are cleared,
or an asserted observation is current. Do not infer whole M-05 or Phase 3
completion.

## Numeric compatibility

Fact shapes use Decimal128(38,18), supported by the existing Arrow/Parquet and
DuckDB stack. Original lexical values, units and declared decimal precision
and scale have separate fields. Projections must prove exact representability
and reject wider values, never round, truncate, drop rows or rewrite the
source-specific package. This version is not a universal carrier for every
possible value admitted by another schema (notably a 21-integer-digit value
with 17 fractional digits). Such values require a separately designed
compatible projection and remain preserved in their existing source layer.

A wider Decimal256 proposal was rejected during self-review because the
locked DuckDB runtime could not register that Arrow type. The failed synthetic
probe is recorded in the run log. No real data was converted. Source units,
price bases and population definitions are not inferred by these shapes.

## Verification scope

The focused tests check the exact registry, field order, metadata, nested-list
names, nullability, unknown-version failure, exact Parquet schema round trips,
DuckDB access to representative numeric values, overflow rejection and a
property over the full representable decimal coefficient range. An initial
round-trip failure exposed Arrow/Parquet list-child naming differences; the
new shapes explicitly use `element` rather than weakening equality checks.

No public file, original source, existing derivative or old schema is modified
by importing or querying this registry.

## JSON transport descriptors

`schemas.health_recordset_json.recordset_json_schema(name, version="v1")`
returns a fresh Draft 2020-12 descriptor for a single row. All columns are
required, nullable columns explicitly admit null, and additional fields are
rejected. Domain, record-set and version constants are enforced. Dates and
timestamps require the caller to enable format checking explicitly.

Decimals travel as bounded fixed-point strings, never JSON floating-point
numbers. The grammar allows at most 20 integer and 18 fractional digits and
rejects exponent notation, leading zeroes, nonfinite values and trailing
newlines. It does not round source values. Unknown Arrow types, names and
versions fail closed. Returned nested dictionaries are independent.

These descriptors remain structural only: they do not prove factual IDs,
rights, source precision, null-reason consistency, time alignment or source
truth.
The separate opt-in [normalization API](./recordset-normalization.md) checks
duplicate/blank IDs, known endpoint ordering and decimal/null consistency while
converting JSON representations exactly. It leaves the descriptors unchanged;
source-specific stable-ID derivation and factual source interpretation remain
separate. No existing source package is converted or promoted. The 51 focused tests
include ten seeded descriptor counterexamples; these are not ten additional
source-code mutant kills. The final unfiltered cold mutation run generated
and killed two source mutants, with no survivors or cached results.
## Main integration receipt — 2026-08-31

Main `25f9fb5` was integrated in an independent clone at `b626b6f`, preserving
the exact incoming ledger prefix followed by the two original schema events.
Production and test SHA-256 remain respectively
`012ef66cbd81c5b5e845bd3deee6c05d04b3b79ff7361b3dcb2c802672acb6c1` and
`dd10a30e2f68da3a289ddcc1d3c8b85de5700f8bedabd593552087b88fbb1952`.
Post-integration 34 focused tests and the 73-track Conductor check pass.
The first focused invocation reused another clone's interpreter without an
explicit source path and failed collection; retry with this clone's `src` on
`PYTHONPATH` passed unchanged code. No shared environment was modified.
The recorded full native pass predates this integration and is not a new
integrated native result. Hosted exact-head checks remain required.

## JSON descriptor delivery integration

PR300 head946e304 was integrated with mainc4d62ca in an independent standalone
clone without changing JSON production or tests. The complete incoming ledger
is an exact byte prefix, followed by the two existing JSON events; every line
parses as JSON.69focused JSON/Conductor tests passed5.97seconds. Production
SHA2561173a96654a18d6b7f0337f34cff79dd17b21b4011a8a92a62ebc1769a113122
and test SHA2563d2973906cec0dacb9d9c4050a4033376393f1e67fad9e47b39872eaad32a0db
match the preintegration head. The prior native pass is retained, not rerun or
relabelled as integrated assurance; fresh exact-head hosted checks are required.

After QES delivery, main6c23ba8 was integrated with unchanged JSON source/tests.
69focused checks passed3.47seconds; every ledger line parsed and the complete
incoming prefix matched byte-for-byte. This second documentation integration
does not reuse the prior head's hosted checks as evidence for its new head.

## Phase 3.1 contract evidence reconciliation — 2026-09-26

The previously open fixture tasks are covered by merged acceptance suites and
their original validation evidence in `eight-recordset-fixture-completion.md`
and `eight-recordset-fixture-completion.json`:
`tests/schemas/test_health_recordset_fixture_acceptance.py` exercises all nine
registered sets (eight domain shapes plus `field_lineage`) through JSON
Schema, Arrow and Parquet; `test_health_recordsets.py` pins versioned fields,
nullability and decimal bounds; `test_health_recordset_normalization.py`
covers binary-as-text and duplicate-key rejection, missing contexts, null
reasons, precision and temporal ordering; linked-fixture and source-adapter
tests close field lineage and stable source IDs; adapter/formula tests retain
unknown layouts and unqualified formula/cache values. Dimension-mapping tests
require explicit evidence for mapped assertions. These are fixture evidence,
not proof of truth or rights. See the Phase 3.1 checklist and paired completion
receipt for exact scope and validation. The parent full validation checkpoint
remains separate.
