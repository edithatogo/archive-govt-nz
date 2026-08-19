# Requirements: Identity, Normalisation, and Corpus Application Service

Track: `legislation_corrective_identity_normalisation_corpus_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#132](https://github.com/edithatogo/archive-govt-nz/issues/132), [#133](https://github.com/edithatogo/archive-govt-nz/issues/133), [#134](https://github.com/edithatogo/archive-govt-nz/issues/134)

## MoSCoW Requirements

### Must
1. **v2 FRBR Model Specification**:
   - Represent FRBR Work (`WorkRecord`), Expression (`ExpressionRecord`), and Manifestation (`ManifestationRecord`) as explicit runtime dataclasses in `src/archive_govt_nz/domains/legislation/models.py`.
   - Support both `to_dict("v1")` and `to_dict("v2")` serialization on `LegislationRecord` with zero schema drift.
2. **Safe Legal Document Normalisation**:
   - Parse XML and HTML byte payloads in `src/archive_govt_nz/domains/legislation/normalise.py` safely without XXE expansion or entity attacks.
   - Accurately infer statutory types (Act, Regulation, Bill, Deemed Regulation, Order in Council) and in-force status.
   - Populate exact byte size, dual CAS hashes (`sha256`, `blake3`), statutory sections, and schedules.
3. **Unified `LegislationArchiveService`**:
   - Provide a single application service in `src/archive_govt_nz/domains/legislation/corpus.py` coordinating adapter capture, API client transport, CAS storage, manifest generation, Parquet/JSONL export, and dynamic coverage reporting.
