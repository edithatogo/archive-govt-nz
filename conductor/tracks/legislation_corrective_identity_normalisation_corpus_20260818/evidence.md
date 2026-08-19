# Evidence: Source-Evidenced, Namespace-Aware Legislation Normalisation

## Executed Commands & Test Receipts

- `uv run pytest --cov=archive_govt_nz.domains.legislation.normalise tests/domains/test_legislation_normalise.py tests/domains/test_legislation.py`: 20 passed, 95.81% coverage.
- `uv run python tools/validate_contracts.py`: All 15 YAML contracts validated.

## Invariants Verified

- Zero regular-expression tag stripping in HTML extraction (uses bounded `_SafeHTMLTextExtractor`).
- XML external entity declarations and billion-laughs attacks defeated via `defusedxml`.
- Namespace awareness across NZ legislation schemas (`http://www.legislation.govt.nz/namespaces/legislation`).
- Zero defaulting of statutory type to Act or legal status to In Force.
- Explicit non-zero status uncertainty for unevidenced documents.
