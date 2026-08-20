# Review

Local implementation review: accepted at `c92850b`, subject to rerunning the
exact OSV audit lane when its external service is responsive.

- Sync has one implementation path through `LegislationArchiveService`; the
  CLI no longer performs direct acquisition or injects a default work.
- Discovery is explicitly search-derived and empty/error results are non-zero.
- Validation, manifest inspection, and coverage require an authenticated
  discovered inventory. Coverage uses discovered work IDs as denominator.
- Operational status and replay require mutually linked manifest, checkpoint,
  and production-sharded CAS state with dual hashes and byte counts.
- Change reporting remains unverified without a real event ledger.
- Publication planning is policy-blocked and token presence is never treated
  as remote verification or rights clearance.
- Unknown `nzlc` actions fail with exit 5 rather than silently invoking status.

The full repository harness cannot yet be called green because its required
OSV transport failed repeatedly. Publication, rights, MCP, workflow, live
operation, recovery, cutover, and donor archival remain unresolved. This
branch must remain local until its service and global CLI predecessors merge in
order and the merge freeze is lifted for the next single PR.
