# Fiscal Gold cross-product query matrix

The bounded DuckDB query matrix reconciles the admitted nominal, GDP-share,
per-capita, and household-CPI benchmark rows for FY2024 and FY2025. It checks
shared health source IDs and amounts, exact GDP denominator IDs, population
lineage and the missing-population status, plus the four quarter IDs feeding
each CPI benchmark. Queries remain read-only and use exact decimal encodings.

The API continues to reject a `real` table. The household-CPI product is a
purchasing-power benchmark and has not been approved as a health-spending
deflator. CPI base, GST treatment, fiscal-period comparability, and source-rights
qualifications do not support that derived view yet. This bounded matrix does
not reconcile the separate Crown, Budget, revision, classification,
department/portfolio, or CPB products.

Focused validation passed: `tests/domains/health_appropriations/test_fiscal_analytical_operations.py`
(11 tests).
