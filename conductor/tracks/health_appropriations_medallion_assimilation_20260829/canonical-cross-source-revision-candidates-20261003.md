# Canonical cross-product revision candidates (2026-10-03)

Canonical Gold revision reporting now covers Budget, revenue, Pharmac, Ministry
of Health indicators, and Crown expense facts. Each report compares exact
within-product source context and literal period tokens across observed
vintages. Changed candidates retain source record IDs and exact Decimal text;
duplicate groups are counted as ambiguous and are not interpreted.

In the clean-room build, the historical report found 106 shared
series-periods: 98 unchanged and 8 changed candidates. Budget found 93 shared,
all unchanged. Crown found 10 shared, 5 unchanged and 5 changed candidates.
The supplied vintages had no exact shared keys for revenue, Pharmac, or MoH.
All reported ambiguous counts were zero. These observed counts do not establish
that the sources have complete vintage coverage.

The report does not explain changes or establish comparability across products
or vintages. The 30 historical donor differences remain blocked and
unapproved; no values were replaced. Rights and publication remain unevaluated
and unperformed. The clean-room receipt records actual product-level counts and
whether the Bronze CAS remained unchanged.

Validation: focused consumer, canonical Gold verifier, and recovery tests;
`./scripts/validate.sh`; and automatic Conductor `phase_7_gates` review. The
configured coverage floor is 80%; no tests were added to raise coverage.
