# Vote Health Supplementary Estimates category totals, 2007/08

Phase 5 now has a local Silver profile for the captured 2007/08 Supplementary
Estimates and Supporting Information PDF. The 36-page source is recorded in
the census as `treasury-vote-health-pdf-f1a09322538d8791`, pinned to SHA-256
`e76311821f75c2b02c82c8c63d771b9948eb0547caa1af40df662213588ec9f8`.

The adapter covers only the six printed category totals on pages 2–6. This
edition labels Crown other expenses and departmental/Crown capital expenditure
differently from adjacent years; those source labels remain verbatim. It
preserves the three `$000` budget columns, parenthesized adjustments, the
printed dash as a null value with raw token lineage, 18 field-lineage rows, and
five partial-page dispositions.

Two independent clean-room Bronze builds are byte-identical and match the
persistent Silver package; the receipt confirms Bronze remained unchanged.
The broader recovery is still `partial_with_blockers` for other sources and
products. Treasury's CC BY 4.0 notice is recorded, but normalized-fact rights
remain `not_evaluated`. No currency interpretation, cross-edition comparison,
Gold measure, federation, or publication is asserted.

See the machine receipt and clean-room recovery receipt linked from `index.md`.
`./scripts/validate.sh` passed with exit code 0: 7,629 tests passed, 10
skipped, 97.55% coverage against the 80% floor, 56 schemas and 46
representative documents, 9/9 differential parity, and mutation, security,
and supply-chain gates all passed. The initial lint-only PT018 finding and its
fix are noted in the machine receipt.
