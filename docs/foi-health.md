# Read-only shared queue health

`tools/foi_health.py --receipt build/foi-shared-health.json` reads one verified
GitHub control snapshot and records its exact authority commit. It does not create
state, renew ownership, release leases, retry jobs, capture sources or publish data.
Use a GitHub token with read-only contents permission when supplied through
`GH_TOKEN`; without it the read is anonymous and subject to the lower shared API
rate limit. Tokens, document bodies and exception messages never enter receipts.

Health fails when any source has pending or leased jobs and an expired owner, or
when any capture lease has expired. Completed `captured`, `verified` and exhausted
jobs do not fail merely because their historical owner has expired. Expiry is a
signal for evidence-based operator reconciliation, never permission to release a
lease or advance queue credit.

Capacity fails at 90 percent of the 1 MiB state limit or a sum of source versions
of at least 9,000 against the 10,000-generation cap. Both capacity measurements are
explicitly estimates: the current backend exposes documents and their versions,
not the original envelope's global generation. The byte estimate reconstructs the
canonical envelope using the version sum. A green estimate does not establish
unlimited capacity or replace backend enforcement.

Reports contain counts, finding classes and at most 50 affected source IDs, with
an omitted count so detail limits cannot hide failures. Receipts are capped at
64 KiB and created exclusively with private file permissions; a missing parent
is created. Existing receipts are never overwritten. Fetch/validation failures
produce sanitized class-only failure receipts. If receipt writing fails, sanitized
stdout still records the failure, which exits nonzero. Configure workflow artifact
retention with an always-run upload step, and preserve the job log if local disk
failure prevents artifact creation.

The client has 10-second HTTP timeouts, no redirect following and no implicit proxy
or environment authentication. The workflow supplies an outer wall-clock timeout
including dependency installation; socket timeouts alone are not a total job
runtime guarantee. These health checks are operational diagnostics, not country
completeness, public-restore evidence or authority to activate capture.
