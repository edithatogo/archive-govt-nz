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

This is a structural contract only. Arrow does not enforce constant values in
the domain/record-set/version columns, unique or correctly derived IDs,
null-reason consistency, temporal alignment, classification evidence, rights,
or cross-record lineage closure. Semantic row validators, stable identity
construction, explicit source projections, fingerprints and operational
registration remain pending tasks. Do not infer M-05 or Phase 3 completion.

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

These descriptors remain structural only: they do not prove IDs, rights,
source precision, null-reason consistency, time alignment or lineage closure.
No existing source package is converted or promoted. The 51 focused tests
include ten seeded descriptor counterexamples; these are not ten additional
source-code mutant kills. The final unfiltered cold mutation run generated
and killed two source mutants, with no survivors or cached results.
