# Donor PDF bounded visual review

The parent independently verified SHA-256
`620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8`
and rendered physical pages 1, 253 and 267 with Poppler, then inspected the
rendered images. No source bytes were changed or copied into Git.

- Page 1 visibly identifies Budget 2003, dated 15 May 2003, Supplementary
  Estimates of Appropriations for the year ending 30 June 2003.
- Page 253 (printed 235) shows Vote Health Part B1, 2002/03. Main Estimates,
  Supplementary Estimates and Cumulative Vote each have Annual and Other
  columns, all labelled `$000`. Negative adjustments use parentheses; dashes
  appear in distinct amount cells. Wrapped purpose/reason text is a separate
  column and must not be interpreted as additional amount cells.
- Page 267 (printed 249) shows Part F1 Crown Revenue and Receipts, 2002/03.
  Main, Supplementary and Total Budgeted are three distinct `$000` columns.
  Parenthesized adjustments and dashes must retain their source semantics.

The images corroborate the identity mismatch and the two different table
layouts. This is not a visual review of every Health page, a completed PDF
adapter or numerical admission. Continuation rows, all table boundaries, signs,
dash semantics and source notes still require a bounded tested extraction
contract. The filename cannot supply a 2024/25 vintage.

Reproduction: `pdftoppm -f PAGE -l PAGE -singlefile -scale-to 1600 -png
CAS_PATH TEMP_PREFIX`, for PAGE 1, 253 and 267. Temporary renders are local
review aids, not canonical outputs or rights/publication approval. The PDF
skill required image inspection rather than relying solely on extracted text.
