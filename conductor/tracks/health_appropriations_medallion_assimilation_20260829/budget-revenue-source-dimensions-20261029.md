# Budget revenue source-literal dimension assertions

Phase 3.2 progress for issue #209. The edition-bound Budget revenue common
adapter emits unresolved source-literal assertions and occurrence links for
vote, department, revenue type, amount type, displayed amount unit and year.
The unit is bound to the Raw Data column header; the other literals are bound
to their source row cells. Explanation-sheet duplicates are retained in the
original field lineage but excluded from this literal projection. No canonical
crosswalk, currency, period alignment or rights grant is asserted.

The synthetic 2025 workbook dispatch checks exact source values and coordinates,
unresolved targets and identical repeated outputs. The adapter and affected
revenue and context dimension suites pass 58 tests. Source bytes, numeric tokens,
existing native package outputs and source lineage are unchanged. Other source
families, real-source repeat evidence and the integrated Phase 3 checkpoint
remain open.
