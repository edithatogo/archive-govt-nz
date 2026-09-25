# Budget versus Estimated Actual diagnostic

The Budget analytics now produce a source-label comparison between `Budget`
and `Estimated Actual` facts. Comparisons are grouped by source object, edition,
year, functional classification, department, portfolio and unit. Each output
retains exact contributing record IDs, preserves unmatched categories as
explicit missing-side states, and computes the exact estimated-minus-budget
difference only when both source labels are present.

This is an edition-bounded diagnostic. It does not establish fiscal-period
alignment, classification crosswalk validity, or final actual expenditure;
`period_basis` remains `unverified`, and the output is not a published Gold
product. Focused contracts are in
`tests/domains/health_appropriations/test_appropriation_analysis.py`.
