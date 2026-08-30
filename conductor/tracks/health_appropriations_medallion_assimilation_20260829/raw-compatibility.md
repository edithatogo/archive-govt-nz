# Source-derived compatibility projection

Status: projection validated locally; persistent export and full task acceptance
remain pending. This is not a replacement for the donor-derived publication.

`raw_compatibility.project_record` maps canonical records to the five legacy
table shapes. It requires known profile/measure/unit combinations, exact integer
years, source identities and finite Decimal amounts. INTEGER columns reject
fractional and out-of-range values; REAL conversion flags every exact binary
representation difference. Original decimals are retained as strings alongside
the full source context. The pure projection never reads or writes files and
does not substitute for verification of the containing run or field lineage.

The existing verified raw run projects to:

| Table family | Rows | Binary representation differences |
| --- | ---: | ---: |
| Recent appropriations | 215 | 0 |
| BEFU Health | 10 | 0 |
| HYEFU Health | 10 | 0 |
| Historical Health | 53 | 15 |
| Historical GDP | 53 | 0 |

There are 341 raw facts, compared with 312 donor-derived records. The existing
historical reconciliation explains 29 restored annotated-year observations and
one exact source/donor decimal difference. The 15 binary representation flags
are a separate storage property, not 15 source disagreements or corruptions.

## Next integration contract

- Verify the raw run against its exact manifest and original CAS, then parse
  capped, hash-verified snapshots of each stage's facts and lineage.
- Require unique record identities and matching amount lineage; retain every
  source fact and exact decimal in sidecars. Do not silently deduplicate.
- Reserve a new exclusive output directory outside both Bronze and the input
  run. Never reuse the old export helper's unlink/overwrite behavior.
- Write the five fixed-schema SQLite tables, check integrity, and produce a
  versioned manifest pinning the raw input, policy, output hashes and counts.
- Preserve failures without a completion claim. Test interruption, existing
  output rejection, tampering and independent deterministic rebuilds.
- Compare with the unchanged donor oracle using explicit repair dispositions.
  Do not describe the 341-row product as exact 312-row donor parity.
- Continue source-derived analytics with period/basis and denominator guards.
  New candidate publication needs its own exact-manifest approval.
