# Pure canonical Budget appropriation projection

`project_budget_appropriations` composes the existing public, pure Budget
classification projection. It adds canonical `appropriation_fact` rows and ten
field links per fact to the unchanged source-label occurrence dimensions and
their existing one-link-per-fact lineage. Inputs remain caller-verified retained
Budget 2025/2026 extraction tables; this function performs no I/O or fixity work.

| Source field | Canonical targets |
| --- | --- |
| amount | amount, value_token |
| year | period_token |
| department | department |
| appropriation_name | appropriation, source_label |
| portfolio_name | portfolio |
| amount_type | amount_type |
| raw:Vote | vote |
| functional_classification | classification_ids |

Source `Decimal(20,3)` is copied exactly into the registry's `Decimal(38,18)`.
No rounding or binary conversion occurs. `value_token` retains the extraction
lineage token, not an independently verified literal original OOXML token.
Amount lineage normalization uses the canonical carrier's 18-place text, while
the original extraction token is retained separately. The inherited parent's
20,3 consistency checks run inside an explicit 50-digit local Decimal context,
so caller precision/traps cannot silently change validation; the caller context
is unchanged. Wider source schema variants fail closed.

Numeric token/value divergence is rejected rather than silently repaired. The
inherited `exact_number` validator quantizes only to test equality, returning
no accepted value when precision would be lost. A public negative case with
consistent raw JSON/lineage `1.2345` and normalized source amount `1.234` is
rejected by that parent contract. Numerically equal trailing-zero token `1.2300`
is retained verbatim. Acceptance is bounded, not a claim that every possible
package or arbitrary extraction token is supported.

Year tokens and amount types are retained. Valid start/end dates remain null
and `valid_time_status` is `not_established`. Adapter measure/unit are inherited;
currency, price basis, base period and denominator remain unestablished. Source
observation context is retained, not newly attested as capture time or proven
observation-ID preimage. Classification IDs reference separate unmapped source
label occurrences, not authoritative codes or an inferred crosswalk.

Facts explicitly flag unmapped classification labels, inherited adapter units
and unestablished currency. `inherited_field_scope` identifies adapter unit and
measure assertions, physical Arrow precision/scale and the limited caller
observation context. These clarify provenance without new semantic inference.

Canonical IDs include transformation, manifest pin, original hash, vintage,
source record identity and role. Input row order does not change output. Every
original lineage accounting ID from the parent is retained, with new target
links appended; unmapped fields remain explicitly retained-only. All 25 source
fact fields have explicit mapped/retained accounting. Caller source-package
retention remains necessary; the projection is not an archive replacement.

Rights remain `not_evaluated`, authoritative mapping is `not_performed`, input
fixity is `not_performed`, and publication approval is `not_granted`. Existing
source v1 packages, originals and publication candidates are not rewritten.

## Assurance in progress

The initial import failed before implementation. A new full-field/lineage test
then exposed source-scale versus canonical-scale amount text; it failed before
the 18-place normalized representation was added. The extraction token remained
unchanged. Current focused tests include exact source extrema, zero/negative
amounts, caller Decimal precision 2, schema/nullability, complete accounting,
input immutability/order, vintage/pin identity separation and invalid source
metadata/lineage. Critical coverage is 100% across 79 statements / 16 branches
with the expanded focused suite; typing and Ruff pass. Parent-requested
provenance flags and the inherited-field receipt each failed a regression test
before being added. Independent review found no further arithmetic, identity
or accounting issue. Cold mutation and the
full native harness remain required before PR delivery.
