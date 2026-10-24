# Crown projection to Gold reconciliation

The source-separated Gold package now emits
`crown_projection_gold_reconciliation.json` when BEFU, HYEFU, or historical
Fiscal Crown facts are present. For each emitted row it retains the source
record ID, Gold record ID, source-object digest, source vintage, literal period,
measure, amount type, unit, source numeric token, and Gold Decimal value. The
builder requires unique source and output identities and exact Decimal equality
between the retained token and Gold amount. Package verification recomputes the
report from the pinned Parquet tables and requires its payload and product
copies to agree.

The report is an internal projection control. It does not recalculate the
official publisher's totals, compare source vintages, aggregate Crown measures,
assert currency/accounting-basis equivalence, or evaluate rights or publication.
The BEFU and HYEFU years remain literal labels with unqualified boundaries; the
historical Fiscal Crown source's core and total measures remain separate.
