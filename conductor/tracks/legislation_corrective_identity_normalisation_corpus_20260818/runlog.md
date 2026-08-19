# Run Log: Identity, Normalisation, and Corpus Application Service

- Implemented `WorkRecord`, `ExpressionRecord`, and `ManifestationRecord` in `src/archive_govt_nz/domains/legislation/models.py`.
- Upgraded `LegislationRecord.to_dict()` with `to_dict_v2()` schema conformance.
- Enhanced `src/archive_govt_nz/domains/legislation/normalise.py` with safe XML/HTML extraction and v2 metadata fields.
- Implemented `LegislationArchiveService` in `src/archive_govt_nz/domains/legislation/corpus.py`.
- Added test coverage in `tests/domains/test_legislation_corpus_service.py`.
