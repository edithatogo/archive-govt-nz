# Vote Health Bronze-to-Silver recovery (2026-10-03)

Two eligible captured Treasury Vote Health PDFs now have locally verified
Bronze-to-Silver paths. The 2002/03 Estimates PDF uses a pinned detail-only
profile: 27 Part B1 facts and 162 field-lineage rows. Two fresh builds matched
the retained Silver Parquet output hashes; the original Bronze bytes were
unchanged. The recovery receipt is
`vote-health-estimates-2002-03-recovery-20261003.json`.

The 2003/04 Supplementary Estimates PDF uses separate exact-layout profiles for
its Part B summary, Part B1 detail and Part F revenue. The retained local Silver
profile set contains 9 summary facts, 26 detail facts and 17 revenue facts.
Two builds per profile produced identical manifests and Parquet bytes. The
registered Bronze adapter selected the source uniquely and its 52 records
matched the combined Silver products by record ID and all fields. The adapter
receipt, lineage and loss counts and consolidated checksums are in
`vote-health-silver-2003-04-20261003.json`; the Silver products are retained
under the external Health archive's
`silver/raw-vote-health-supplementary-2003-04-20261003-v1` directory.

Both products preserve source labels and page/cell lineage. Rights remain
`not_evaluated`, publication remains local-only, and no analytical mapping or
cross-vintage equivalence is asserted. This does not cover the remaining
captured Vote Health PDFs, other layouts, unretained vintages, or complete
annual Budget series. The overall Phase 5.2 task remains open.
