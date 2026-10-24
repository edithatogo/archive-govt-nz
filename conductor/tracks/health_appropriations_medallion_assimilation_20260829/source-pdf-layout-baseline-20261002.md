# Captured-source PDF page-layout baselines

This report fingerprints page geometry and structural resource counts for
official PDFs linked from the pinned census, capture manifest and Bronze CAS.
The builder verifies captured-byte identity before parsing. It records metadata
keys only and does not extract or publish page text.

The capture contains 58 PDF sources. Strict parsing produced page-layout
baselines for 55; three PDFs are encrypted and remain unavailable without
decryption. The parsed set contains 54 distinct structural fingerprints in
the shared `treasury_vote_health_document` family. This variation is an
observation only; it does not approve normalization or assert semantic change.

The fingerprint is limited to page count, media/crop boxes, rotation, resource
category counts, annotation counts and metadata keys. It does not assess text,
typography, tables, semantic structure, within-page layout, rights or discovery
completeness. Ten of the 74 captured sources are neither among the six
workbook-inventoried sources nor these 58 PDFs and remain without layout
baselines.

Machine evidence: `source-pdf-layout-baseline-20261002.json`, SHA-256
`1f9eb496f6291347daf9c8546c3fad7c9e7ac977a808e74a6b468c6221608032`.
Reproduce it with `tools/health_pdf_layout_baseline.py`, the pinned
`source-census.json`, the external capture manifest
`official-capture-2026-09-30-health-refresh.json` and the external Bronze CAS.
The focused suite covers structural variation/repeatability, Bronze fixity,
source identity, non-PDF exclusion and unavailable encrypted/malformed PDFs.
