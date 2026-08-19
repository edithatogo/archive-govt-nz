# Run Log: Identity, Normalisation, and Canonical v2 FRBR Model

- Implemented `LegislationWork`, `LegislationExpression`, `LegislationManifestation` and deterministic ID generators in `src/archive_govt_nz/domains/legislation/identity.py`.
- Removed all default fixed timestamps from `LegislationRecord` and model definitions in `src/archive_govt_nz/domains/legislation/models.py`.
- Implemented `RelationshipRecord`, `RelationshipType`, and `ProvenanceReference` for enriched legal metadata.
- Implemented `convert_v1_to_v2`, `convert_v2_to_v1` with explicit lossy conversion reporting, and `validate_legislation_record` schema validation.
- Validated 97.79% test coverage on `models.py` and `identity.py`.
