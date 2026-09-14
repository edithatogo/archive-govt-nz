# Budget 2025 Health revenue canonical projection

This increment adds the additive `revenue_fact` canonical recordset and a pure
projection from the existing hash-pinned Budget 2025 Health revenue extraction.
It preserves the source `Revenue Type`, `App ID`, Vote, Department, description,
amount token, period end and field-level source coordinates. The projection
declares `netting: prohibited`; it neither emits an `appropriation_fact` nor
aggregates revenue with expenditure.

The projection accepts only the established source-specific extraction schema,
its manifest contract and complete normalized-row accounting. It rejects schema,
manifest, type and numeric-token drift before producing canonical tables.

Validation for this increment:

```text
152 passed
tests/domains/health_appropriations/test_budget_revenue.py
tests/domains/health_appropriations/test_budget_revenue_projection.py
tests/schemas/test_health_recordsets.py
tests/schemas/test_health_recordset_json.py
```

This is a scoped Budget 2025 revenue addition. It does not complete Phase 5.2:
the Treasury Vote Health Estimates/Supplementary Estimates tables and the
remaining annual Budget editions still require source-specific promotion.
