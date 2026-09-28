# Canonical Gold source drill-through

The source-separated Gold manifest now includes a deterministic index from
each admitted Silver `input_record_id` to every canonical Parquet table row
that contains it. Each reference carries the exact Parquet SHA-256 and its
zero-based row index in the query's sorted output. Historical observations,
historical coverage, nominal Budget, and nominal revenue remain separate
outputs; the index performs no joins or mapping.

This provides package-level drill-through to the exact Silver record
identity. It does not add source-page coordinates, certify source rights, or
claim analytical completeness. Existing row-level and aggregate product
semantics remain unchanged.

## Verification

- The new assertion failed before implementation because the manifest had no
  drill-through index.
- The focused canonical Gold test now reads each referenced Parquet row back,
  confirms the input ID is present, and verifies the file hash matches the
  manifest output inventory.
- Canonical consumer suite: 15 passed; Ruff and basedpyright passed.
- Full repository validation: pending.
