# Forecast source-literal dimensions

The BEFU 2026 and HYEFU 2025 common adapters now emit source-literal
functional classification, measure, amount type, unit and period assertions,
with a link for each admitted fact and exact source coordinate. Labels are read
from field lineage: for example the unit assertion retains `($millions)` rather
than promoting the normalized `NZD_millions` as a source literal. Every target
remains unresolved, including period calendar bounds and crosswalks. Rejected
formula cells do not gain dimension links.

On the two retained Bronze workbooks, each profile produced 10 facts, 15
assertions and 50 links. Independent repeated dispatches matched and original
SHA-256 values remained unchanged. The canonical assertion and link JSON hashes
are `b48756c17e2fbdbd2d6dc9713ee399965eb12975f6bf93a5396ca3fceb295f01`
(BEFU 2026) and `f7e5bbe803c62488ab298fedf3b07a76e9f8796cde7df0c27348511c347cef7b`
(HYEFU 2025). Focused adapter and context-dimension tests passed. This does not
approve mappings, currency, fiscal alignment or the broader Phase 3 checkpoint.
