# Historical workbook source-literal dimensions

Issue #209: the pinned Fiscal 2024 workbook adapter now retains unresolved
source assertions and links for year labels, measure labels and unit headers.
These use exact source cells and do not assert crosswalks or rights. Existing
fact values, field lineage and loss descriptors are unchanged.

Two dispatches of the retained Bronze object
`769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d`
produced identical results: 106 facts, 318 links and 85 unresolved assertions.
The source hash remained unchanged. Fixture checks cover source labels,
unknown bytes, layout refusal and repeat output. This does not qualify other
workbooks or close the Phase 3 integrated checkpoint.
