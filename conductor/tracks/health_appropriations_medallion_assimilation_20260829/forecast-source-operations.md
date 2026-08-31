# Forecast successor source operations

## Bounded contract

This M15/M18, AC13/AC16 increment adds only `befu-2026/v1` and
`hyefu-2025/v1` to the existing source-operation dispatcher. Legacy forecast
aliases are not exposed. It preserves the five source-specific counts
(normalized, rejected, context, preserved_only, inventoried_cells) and the
forecast_facts, field_lineage and cell_dispositions Parquet outputs.

Actual and Forecast remain distinct supplied amount types. No annual joins,
canonical projection, inflation adjustment, rights decision, source acquisition
or publication is performed. Default CLI operation and all MCP operations are
read-only; explicit local writes retain exclusive new-output behavior. A partial
adapter result is a failed compact receipt, never a successful preflight.
Preflight verifies adapter execution, not successful serialization or publishing.

## Dependency and source boundary

Development started on PR313's six-profile dispatcher and locally cherry-picked
the forecast API-only checkpoint `a85ca415544b1367c9f786ca6bfab174b5d54c73`
as `151c049`. Both dependency deliveries remain separate from this work.
The initial short-SHA local fetch failed without changing source; the resolved
full SHA fetched successfully. A plan-only cherry-pick conflict retained both
approved tasks and the existing completed four-profile delivery.

The only adapter change in this increment is a public `TRANSFORMATION` alias
for the existing unchanged identity. No private helper is imported, no parser
behavior changes, and the API's legacy default-write behavior is unchanged.

## Local evidence

The newly allowed BEFU preflight first failed as an unsupported profile
(one expected failure, 5.62 seconds). After implementation, all eight profiles
passed 277 tests. Added independent direct-adapter/package byte comparisons and
literal-versus-formula partial-result tests for both successors brought the
suite to 279 passing tests (13.40 seconds). Tests preserve original bytes and
prove Actual/Forecast labels remain unchanged. Ruff and strict types pass.

Critical line/branch coverage is 100%: 70 statements, 16 branches, 279 tests
in 13.53 seconds on CPython 3.14.6. Dispatcher SHA-256 is
`613c077ce95bc4c735e0ce90efc3e2d36f3e55237a5f0bc0f239e31b120ff5b6`;
test SHA-256 is
`d3661b21538c4e8cc433a41474e637e6af0402ef9813e4a8887f1d7f3e350d41`.
Cold mutation, native harness, dependency integration and hosted checks remain
pending. No real source payloads are committed or used by these tests.
