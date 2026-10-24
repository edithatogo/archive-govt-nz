# Vote Health 2002/03 Part F revenue

The exact retained Estimates PDF has a separable Part F revenue table on pages
43–44. Its columns are 2001/02 Budgeted, 2001/02 Estimated Actual and 2002/03
Budget. The new profile preserves these meanings as distinct decimal fields;
it does not reuse the 2003/04 main/supplementary column semantics.

The source census identifies the 317,126-byte PDF as
`treasury-vote-health-pdf-fd37e5ad2657936d`, SHA-256
`1170e0bf5d11e6ac93620a2d76d68004ed99b88ed45a0c6c3c48bbc38f72fafe`. A
hash-pinned parser emits 16 revenue facts, 48 source-field lineage rows and two
page dispositions. Two full Silver builds have byte-identical manifests and
Parquet outputs. The expanded unique Bronze adapter emits the 27 existing
Part B1 detail records plus these 16 revenue records; all 16 revenue records
match Silver by record ID and every emitted field. Its 44 page dispositions
account for all source pages, and the source bytes remain unchanged.

The retained source census records CC BY 4.0 and the Treasury policy URL; this
work does not adjudicate rights. The facts are a local derivative only. The
2002/03 narrative summary, other Vote Health editions, year-wide completeness,
canonical Gold projection, currency qualification and cross-source comparison
remain open. The machine receipt and full output hashes are in
[`vote-health-revenue-2002-03-20261003.json`](./vote-health-revenue-2002-03-20261003.json).

Focused source, operation, adapter and dispatch tests passed (493 passed, 10
skipped). The required full repository harness passed with 7,300 passed, 10
skipped and 98.10% coverage against the 80% configured floor. Schema, parity,
mutation and supply-chain gates also passed. Automatic Conductor `phase_7_gates`
review passed. Hosted PR checks remain pending.
