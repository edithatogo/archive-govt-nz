# Canonical classification label-change candidates — 2026-10-01

The canonical Gold manifest now includes `classification_drift_report` for
Budget appropriation and Budget revenue products. It groups only within a
source family and an exact observed key (period, amount type, unit, Vote,
department, and portfolio or revenue type), then lists multiple labels seen
for that key across supplied vintages.

A row is a `source_label_change_candidate`, not a confirmed classification
drift or mapping. The report explicitly records `mapping=not_inferred`,
`semantic_equivalence=not_assessed`, and `completeness=observed_rows_only`.
It does not join source families, infer missing periods, compare unrelated
labels, or alter source data. Historical, Pharmac, Crown, and MoH
classification drift remains outside this report because their comparison keys
and alignment policies are not yet approved.

The canonical Gold verifier requires the report schema and its non-inference
boundary. Focused checks cover an exact-key label change, separation by Vote,
and fail-closed rejection of a malformed report. Repository coverage remains
subject to the configured 80% floor; this work adds only those focused
contracts.
