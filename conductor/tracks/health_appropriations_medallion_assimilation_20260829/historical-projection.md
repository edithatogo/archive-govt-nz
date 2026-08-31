# Pure historical Health/GDP canonical projection

This is a bounded M-05/M-06/M-07 implementation, not completion of those
requirements. `project_historical` accepts caller-supplied historical facts,
field lineage, dispositions and extraction metadata. It returns two canonical
fact tables, canonical field lineage and complete original-lineage accounting.
It performs no I/O, input fixity verification, publication or rights assessment.
Callers must verify and retain the complete original package independently.

## Exact contract

- Accept exactly the historical writer schema or its known Parquet transport
  variant (only `quality_flags` and `footnotes` list child names change).
- Retain exact value and original token. Decimal38/17 source values must fit
  Decimal38/18 without rounding, using integer coefficient tests independent of
  ambient Decimal precision. Wider values fail closed, never become floats.
- Include the full source hash, vintage, caller manifest identity, source record
  ID, record set and transformation version in new identities. The supplied
  manifest digest is syntax-checked, not a fixity attestation.
- Keep unknown starts null, exact March/June end dates and literal period labels.
  Require both original date dependencies. No financial-year aggregation,
  denominator alignment or cross-accounting-basis comparability is inferred.
- Check exact amount/year/unit/measure/basis dependencies and source-cell joins.
  Disposition JSON string values must match literal lineage text; the source
  number format is a cell attribute and is the explicit exception. No binary
  numeric coercion is used.
- Require known-unused donor/department/appropriation/classification/portfolio
  fields null. Unknown non-null source fields cannot silently disappear.
- Map amount/token/period/unit/measure/basis/end-date lineage. Every original
  lineage row has a stable mapped or retained-only accounting entry; each mapped
  entry lists its output IDs. Year, month, number format and footnotes remain
  retained-only where no canonical field exists. Original `raw_values_json`
  remains in the retained source table. Disposition reasons and unselected cells
  likewise remain in the retained package, not a newly interpreted inventory.
- Preserve original observation metadata and rights `not_evaluated`. Currency
  NZD follows the reviewed `$ millions` source context. Price/base/denominator,
  institutional coverage and seasonal adjustment remain null; no licence,
  source-acquisition, analytical or publication approval is inherited.

## Reviewed in-memory pilots

No original or derivative files were changed. Outside the pure API, the two
manifest pins and all six listed Parquet hashes were checked before loading.
Original workbook fixity is outside this pilot (the separate snapshot reader
has its own evidence).

| Retained package | Manifest SHA-256 | Health/GDP facts | Output lineage | Original lineage accounted |
| --- | --- | --- | --- | --- |
| raw-historical-20260830-v1 | `2f39ad4dbeb7cb872118ddc634985b5e21b18f2ef2421ca3c0a1e9bf90411288` | 53 / 53 | 1007 | 1143 |
| raw-historical-2025-20260831-v1 | `aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a` | 54 / 54 | 1026 | 1164 |

The first live pilot failed closed on the exact leading-space context
` March Years`. A new regression reproduced it before the explicit reviewed
label was added; arbitrary whitespace normalization was not introduced.
Both pilots then passed, including after the independent review corrections.

## Assurance chronology

Initial import failed before implementation. Additional red tests caught eight
raw-dependency/normalized-cell gaps, Decimal display padding in mapped lineage,
and the two known Parquet child names. These failures were fixed before the
corresponding green runs. Independent read-only review then found contradictory
disposition text and six potentially lost non-null fields; nine new negative
tests all failed before correction. Re-review reported no additional finding.
Two year-boundary fixture updates initially omitted synchronized disposition
literals; correcting the fixture restored the positive controls.

Current focused gate: 121 tests, including a property over exact integer
coefficients, passed; 100% of 184 statements and 32 branches covered. Ruff and
targeted typing pass. Cold unfiltered mutation passed all 129 mutants with zero
survivors, timeouts, errors, pardons or cache hits (one worker, 121 tests,
164.86 seconds). The unchanged deadline was 30 seconds. The coverage-collection
warning does not imply filtered test selection: coverage filtering was explicitly
disabled. The native repository harness passed in the independent clone on
Python 3.14.6/uv 0.11.8: 2,866 tests, eight existing warnings, 97.08% overall
coverage, 41 schemas/31 samples, parity 9/9, all repository mutation controls,
hygiene, audit, licences, secrets and SBOM (111 components). Test stage took
76.99 seconds. This precedes main integration and is not hosted assurance.

Source SHA-256: `f8be15f8501916a712de60b040ba3a1e20b07a854d3fb36bf5f7aefa65be4f28`.
Test SHA-256: `c9d707a73719d83453ceab93cdfa24a67a84e913cb1aec0ec884230412d87003`.
Critical coverage receipt SHA-256:
`b28ed1c438c9422a4fe31891c092f2e90ac2a939a6a62ed0775b0ad994d19d6b`.
Mutation receipt SHA-256:
`3a59033572caaec87024fb8e7df046b3d9d5e3936007920c80e88204fab122ff`.
Native log SHA-256:
`6f0e6f155498ce0bab244eee300222d6d8d985c5c0f93d80ba344d26e9090c7e`.

After merging main `3be3048` into functional checkpoint `596a73f`, the source
and test hashes above stayed unchanged. Integration `47130c2` passed 224 focused
projection/Arrow/JSON/Conductor tests, repository format/lint/types and all 74
Conductor tracks. The complete incoming machine ledger was preserved byte for
byte as a prefix before the two owned receipts. The full native result remains
pre-integration; hosted exact-head checks are a separate gate.
Remaining work includes other source-specific projections, a persisted canonical
package contract and broader semantic validators. This does not canonicalize
unresolved MoH/QES units, rewrite historical packages or advance HF publication.
