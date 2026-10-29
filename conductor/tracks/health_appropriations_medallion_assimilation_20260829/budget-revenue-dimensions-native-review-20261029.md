# Budget revenue dimensions: retained-source review

Issue #209. The Budget 2025 and 2026 revenue common adapters at commit
`2aa0f335a044588ada9dab93a81f6f350521e2a0` were run twice from their
hash-pinned Bronze originals. Both returned identical adapter results. The
2025 source produced 69 facts and 414 dimension links; 2026 produced 70 facts
and 420 links. An independent workbook read checked each link's literal and
cell coordinate against the corresponding Raw Data worksheet, including the
amount unit header. The original source hashes were unchanged.

All dimension mapping targets remain unresolved; currency remains unknown and
rights remain `not_evaluated`. These checks qualify source-literal retention for
two editions only. They do not establish a crosswalk, authorize publication,
qualify other source families, or close the Phase 3 integrated checkpoint.

- `revenue-dimensions-2025-repeat-20261029.json`: SHA-256
  `e70babce05bafed230337705e5b775dff9b033bfaef704511cc0c08fb531641f`.
- `revenue-dimensions-2025-cell-check-20261029.json`: SHA-256
  `14af1062a61881a06b1e47a9de4e2d702e5f46fa0d887c1a5beaa6087165be4f`.
- `revenue-dimensions-2026-repeat-20261029.json`: SHA-256
  `297e1d14aeaa4c7730905108011845728bfa15f9f884c620026f96444c87e5a9`.

These receipts are local source evidence. The repeat verifier and its local
runtime remain in the assurance directory; CI does not possess these Bronze
originals and therefore does not independently execute this native check.
