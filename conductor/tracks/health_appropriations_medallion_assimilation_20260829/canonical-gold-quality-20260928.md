# Canonical Gold quality accounting

The source-separated canonical Gold manifest now contains a deterministic
quality report for admitted canonical records. It enumerates exact input record
IDs by product, reconciles the identities in product tables, and reports
unaccounted inputs. Per-product counts retain the verified package's input
count and output row count.

This report measures provenance completeness only. It does not claim
analytical completeness or source health and explicitly lists classification
drift, revision reconciliation, cross-source reconciliation, and source-health
reports as unresolved. Cross-source joining and vintage pooling remain
disabled. Rights remain unevaluated, and publication is not performed.

## Verification

- Focused canonical consumer suite: 15 passed, including the mixed-family
  build, quality report identity reconciliation, repeat-build byte equality,
  readback, and fail-closed paths.
- Full repository validation: pending.
- Hosted pull request checks: pending.
