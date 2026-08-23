# Requirements: Dataset Identifier Interlinking (MoSCoW)

## Must

- **M-01**: A deterministic interlink builder
  (`tools/build_identifier_interlink.py`) assembles a cross-domain identifier
  manifest from recorded evidence sources (legislation checkpoint, health
  metadata snapshot, publication readback receipt).
- **M-02**: Per-domain identifier shape validation — UUID form for health
  identifiers, HF slug pattern for publications, Zenodo DOI pattern for DOIs,
  non-empty for legislation work IDs.
- **M-03**: Cross-domain collision detection reports identical raw identifiers
  appearing in multiple domains.
- **M-04**: Health resource→dataset relationships recorded in the receipt.
- **M-05**: Stable machine-readable receipt (`archive-govt-nz.identifier-interlink/v1`)
  with per-domain counts, findings, and pass/findings-present status.
- **M-06**: Focused test suite covers loaders, per-domain validation, collisions,
  receipt assembly, and malformed inputs.

## Should

- **S-01**: Pure/offline operation over recorded evidence; no network access.

## Could

- **C-01**: Gazette notice IDs join the manifest automatically once the first
  gazette harvest produces its manifest.

## Won't (this track)

- No modification of upstream identifiers or creation of new identifier schemes.
- No live CKAN/HF queries.