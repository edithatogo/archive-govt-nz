# Phase 3.3 schema drift integration — 2026-10-26

The Bronze workbook baseline already covered all 12 captured XLSX files and
the PDF baseline covered all 59 captured PDFs. Three CSVs and one HTML page
were outside those profiles. They now use their existing reviewed source
parsers and exact captured object pins:

| Source identity | Profile | Structural scope |
| --- | --- | --- |
| `moh_vote_health-008` | HAIR2024 fig27/v1 | exact CSV headers, row count and widths |
| `moh_vote_health-009` | HAIR2024 fig28/v1 | exact CSV headers, row count and widths |
| `stats_nz_cpi-053a0705526fac8d` | CPIQ.SE9A/v1 | exact CSV headers, row count and widths |
| `pharmac_cpb-010` | Pharmac CPB/v1 | reviewed table headers, row spans and required paragraph context |

The [text baseline](./source-text-layout-baseline-20261026.json) binds
census/capture digests, source hashes, layout descriptors, declared fact-schema
fingerprints and complete dispatch receipts. It contains no copied source data
rows. Each Bronze object was re-read and verified on both runs. Rebuilding the
report produced byte-identical JSON; the [drift report](./source-text-layout-drift-20261026.json)
records matching layouts, schemas, selection evidence and ordered outputs.

Previously, the common result types exposed adapter selection and extraction
outputs separately, without an integrated schema/output drift receipt. Both
single-result and native compound dispatch now capture immutable evidence at
the dispatch boundary. This covers every registration returning those result
types: Budget, forecast, context, Pharmac, Vote Health PDFs, donor SQLite,
literal/historical workbooks and HAIR2024, plus native compound profiles.
`to_drift_receipt()` returns a JSON copy without repeating extraction.

Native recordsets retain fingerprints of declared Arrow schemas, including
metadata, schema IDs and versions. Legacy dictionary records report observed
field types explicitly; those observations do not create Arrow declarations.
Decimal/date/byte values receive distinct serialization tags; actual containers
are escaped so ordinary metadata cannot impersonate those tags. The output
encoding is versioned. Record, lineage
and profile order is retained in the output digest, so ordering instability
cannot be hidden by sorting the data. Comparisons report schema/layout
differences separately from changed ordered output. Unsupported or ambiguous
selection remains `preserved_only` and its comparison remains held.

Drift evidence is additive and does not alter earlier Silver package manifests
or output bytes. It is structural/repeat evidence. It does not establish rights,
currency, comparability or normalization approval. Consumers must retain an
independent baseline pin; a receipt digest alone does not authenticate evidence.

`tools/health_text_layout_baseline.py` rebuilds the exact text cohort. Supplying
`--baseline` and `--drift-output` also writes a comparison and returns nonzero
for held or changed evidence. Outputs must be new and distinct, preserving
retained reports. Missing/corrupt Bronze, unqualified pins, unregistered
profiles and parser refusals retain reason-coded unavailable rows.

The [combined v2 reconciliation](./source-layout-reconciliation-20261026.json)
rechecks the existing Bronze workbook/PDF baselines and the new text report.
It covers 75 of 75 captured objects: 12 XLSX, 59 PDF, three CSV and one HTML.
The older Silver-derived workbook baseline remains valid for its original
scope; it is not used to invent gaps already covered by Bronze evidence.
PDF fingerprints cover geometry/resources and HTML covers the reviewed
table/context. Structural coverage does not qualify unsupported source-native
parsers. Remaining adapter coverage and mapping tasks keep the complete
Phase 3 checkpoint open.

Validation commands and outcomes are retained in the runlog and machine
integration receipt. Full validation is required at the reviewable milestone;
focused checks are reused while editing.
