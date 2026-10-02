# Vote Health PDF common adapter (2026-10-03)

Registered one composite Bronze adapter for the reviewed
`Treasury-Vote-Health-Supplementary-2003-04` PDF. A single registration avoids
an ambiguous match because the source document contains three different tables:
the Part B summary, complete six-value Part B1 rows, and the fixed Part F
Crown-revenue table.

The adapter emits the same facts and field-lineage coordinates as the three
existing normalizers. It records every source page as normalized,
partially-normalized, or preserved-only. Hash mismatch, unknown vintage,
encrypted/malformed PDFs, changed page counts, missing sections, and parser
drift fail closed. Other Vote Health editions remain preserved-only; this does
not claim that the 58 captured PDFs or the full 1998–2026 census are covered.
Rights remain unevaluated and no analytical mappings are inferred.

Focused adapter, registry, repeatability, and parser tests passed (23). The
configured coverage threshold remains 80%; tests were added for dispatch,
normalizer parity, loss accounting, fixity, and repeatability rather than to
raise coverage.
