# Evidence: Canonical v2 FRBR Model and Identity

## Executed Commands and Test Receipts

- `uv run pytest --cov=archive_govt_nz.domains.legislation.models --cov=archive_govt_nz.domains.legislation.identity tests/domains/test_legislation_models.py tests/domains/test_legislation.py`: 15 passed, 97.79% coverage.
- `uv run python tools/validate_schemas.py`: 21 schemas validated.

## Invariants Verified

- Zero default fixed timestamps in runtime model definitions.
- Deterministic ID generators without ID fabrication.
- Bidirectional schema conversion with explicit lossy reporting.
