# Source-family guard checkpoint — 2026-09-14

This checkpoint closes the Phase 5.1 guard-test task without treating it as
family-wide normalization or source equivalence.

The established contracts cover the required cases:

- `test_health_historical_source_register.py` preserves dated discovery gaps,
  unknown fixity and unenumerated editions.
- `test_budget_vintages.py` keeps Budget 2025 and 2026 values, periods and
  source digests separate when years overlap.
- `test_dimension_mapping.py` rejects overlapping mappings that differ by
  vintage or version.
- `test_historical_analysis.py` refuses cross-vintage/source splicing and
  reports period, basis and year gaps instead of calculating through them.
- `test_budget_classification.py` preserves unmapped source labels rather than
  asserting a classification equivalence.

These controls describe the exact scope of the completed test contract. They
do not qualify a source for analytical promotion, resolve a rights decision, or
make an unavailable source family operational.
