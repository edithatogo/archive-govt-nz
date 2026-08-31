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

## Local assurance

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
or accounting issue. All 28 cold, unfiltered mutants were killed with one worker,
the unchanged 30-second deadline, zero pardons and no cache hits (37.54 seconds).

The full native harness at `04c923b4c83cc45d469ebe18a3b646608e6b4a40`
exited 0: 3,955 tests / 8 existing warnings / 120.18 seconds,
97.30743538358769% coverage, 75 tracks, 42 schemas / 32 samples, 9 parity checks
and all supply-chain gates including 111 SBOM components. Runtime was
CPython 3.14.6 / uv 0.11.8, with ctrace, JIT disabled and four test workers.
Only two unrelated harness-generated timestamp receipts were restored after exit.
The post-doc check initially used nonexistent `tools/validate_conductor.py`
(exit 2); the actual native entrypoint is `tools/validate_conductor_state.py`.

Frozen source SHA256:
`61630524f4918b1ba611004485de6066da388bc132c5c8c684267bc532e5bd5d`;
test SHA256:
`2ad440d9f0def7df15ab537b51ac5234263b0ddd40d68b1f774723e922e08805`.
Retained native log `/tmp/health-budget-canonical.PIyPZX-native.log` SHA256
`f0028f459995b41ece82a450db555e39f44ef7c9bdd593c543ede0f618e999d9`;
coverage JSON SHA256
`9b24a846e1e6a41fa031b5e38372528fe033d02cc4c9912c7aff620fa15555f5`;
cold mutation JSON SHA256
`5a10ca32abf5c94a31ca6706d47aa176a5e624269114408a80dd858ecb93e45b`.

## Retained-package in-memory pilot

Verified package manifest pins were Budget-2025
`1b1e5dfd3fa90d98dcf5200997001db236df7b40f4404b658c36f5cb0264d2fe`
and Budget-2026
`f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738`.
The public package reader and pure projection produced respectively 215 / 185
facts, 215 / 185 dimensions and 2,365 / 2,035 canonical links. All 6,800 original
lineage entries remain accounted for: 3,200 mapped and 3,600 retained-only.
Reversing every input table preserved results and all three serialized Parquet
byte streams per vintage. Before/after package hashes matched. No original
workbook was reopened and no dataset files, candidates or HF resources changed.
This pilot verifies source-package transport, not new original-file fixity.
Receipt `/tmp/health-budget-canonical.PIyPZX-pilot-receipt.json` SHA256
`156b44b41bb6436c6fab5a4299a69e23b5d32653f0612d6c56ffa382f198969d`.
Exact-head hosted CI and delivery remain separate from these local results.
