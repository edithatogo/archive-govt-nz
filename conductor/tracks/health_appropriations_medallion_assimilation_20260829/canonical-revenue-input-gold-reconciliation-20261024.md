# Canonical revenue input-to-Gold reconciliation

Phase 6 adds a deterministic `revenue_input_total_reconciliation.json` report
for source-separated Budget revenue. The builder reopens each explicitly pinned
canonical `revenue_fact` package, checks that every Gold observation carries
the same record ID, literal source dimensions and Decimal amount, then compares
group totals by source vintage, period token, amount type, unit, Vote,
department, revenue type and source label. Record IDs are disjoint and complete
across the admitted revenue packages; the verifier checks report totals, package
marker membership and equality with the nested revenue-product copy.

The fixture preserves actual revenue and capital receipts in separate exact
period and amount-type groups. Revenue remains a separate product and is never
netted with appropriations. The report records official-source control, donor
control, cross-source comparison, vintage pooling and revenue netting as
`not_performed`; it does not establish source completeness, rights, fiscal
comparability, or analytical approval.

The focused `test_canonical_consumer.py` and
`test_canonical_gold_verification.py` selection passed 72 tests. The exact-tree
`./scripts/validate.sh` then passed on Python 3.15.1: 8,313 passed, 14 skipped,
97.09% branch coverage, 81 schemas/71 representative documents, parity 9/9,
all mutation gates, dependency and licence audits, secret scan and the
115-component SBOM. Exact-head hosted checks and protected merge remain delivery
gates; official-source, donor and cross-source reconciliation remain open.
