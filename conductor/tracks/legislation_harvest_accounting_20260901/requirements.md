# Requirements

- Every in-scope work has exactly one terminal disposition: newly preserved, changed preserved, unchanged revalidated, already processed skipped, unavailable, partial or failed.
- Candidate, scope, attempted and terminal counts must reconcile deterministically.
- Record and CAS before/after totals must reconcile with committed deltas.
- Receipts bind scope digests, parent/output roots, software commit, workflow/run identity, source-response classifications, retry counts and state-commit status.
- A skipped work is never counted as attempted; a source-validated no-change is distinguishable from a checkpoint skip.
- Partial state commits are reported truthfully; commit status is not inferred from overall outcome.
- Corrupt parent state fails before source attempts or state mutation.
- Historical v2 receipts remain readable without synthesising v3 categories or deltas.
- Focused negative, property-based, generated, retry, unavailable, partial, corrupt-parent and mutation tests are required.
