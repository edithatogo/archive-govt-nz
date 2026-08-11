# Implementation Plan

1. [x] Register the track and parent/nested GitHub issue hierarchy.
2. [x] Freeze query, facet, pagination, response, and redaction policy.
3. [x] Implement typed CKAN metadata discovery using bounded HTTPS requests.
4. [x] Add normalized dataset/organisation/resource candidate records and stable
   deduplication.
5. [x] Add relevance, rights, sensitivity, and ambiguity classifications.
6. [x] Add schema-validated JSON/Markdown manifests and evidence receipts.
7. [x] Add property-based, contract, metamorphic, and deterministic-simulation
   tests, including interrupted and repeated discovery.
8. [ ] Run clean-environment validation and review evidence.
9. [x] Hand eligible candidates to a separately approved capture track; do not
   capture or publish from this track.

## Transport compatibility remediation

- [x] Add bounded POST retry and parameter-variant fallback after failure.
- [x] Record parameter variant, page size, status, and response diagnostics.
- [x] Reconcile GET and POST IDs/counts before accepting a fallback result.
- [x] Add contract and metamorphic tests for transport equivalence.
- [ ] Run hosted validation before changing the discovery state from unavailable.

### Options and recommendation

- **Option A — shared-client POST/GET adapter (recommended):** centralizes
  retries, limits, hashing, and error classification. Trade-off: requires a
  larger refactor and contract tests, but preserves one assurance boundary.
- **Option B — discovery-script-only GET fallback:** faster to write, but
  duplicates transport logic and risks inconsistent safety/evidence behavior.
- **Option C — provider endpoint change or alternate official hostname:**
  avoids local transport changes, but depends on external authority and may
  not be available.

Recommendation: implement Option A first. Use Option C only when an official
endpoint is documented and equivalence is evidenced. Do not use Option B.

### Approved implementation contract

- [x] Add a shared request executor inside `BoundedCkanClient`.
- [x] Parameterize only HTTP method and encoding: POST JSON or GET URL query.
- [x] Preserve retry, timeout, response-size, hashing, and error handling in
  the shared executor.
- [x] Add public bounded `action_get()`.
- [x] Add contract tests for POST/GET parity, HTTP-400 fallback, mismatched
  results, and deterministic receipts.
- [x] Wire broader-health discovery to use GET only after POST failure.
- [ ] Run complete local and hosted assurance gates.

Contingencies:

1. If GET succeeds and normalized IDs/counts match POST probes, retain both
   receipts and use GET for the affected scope.
2. If GET succeeds but results differ, retain both as a drift conflict and
   remain `unavailable`.
3. If both fail, retain the bounded diagnostic receipt and continue scheduled
   monitoring without capture or publication.

## Cross-track follow-ups (not Track 12 completion criteria)

- [x] Inspect and preserve the untracked `.entire/` session state without
  deleting user data.
- [x] Complete shared-client POST/GET transport executor and contract tests.
- [ ] Run local and hosted compatibility matrix; retain normalized conflict
  receipts when results differ.
- [x] Resume broader-health discovery only after a stable reconciled receipt.
- [ ] Reclassify Ministry of Health resources from resource-level rights and
  sensitivity evidence.
- [ ] Authorize capture only for explicitly eligible resources.
- [ ] Keep Treasury restricted resources as metadata/tombstone outcomes until
  official access changes.
- [ ] Revalidate staged Hugging Face and Zenodo packages without uploading.
- [ ] Require credentials, rights approval, and release approval before any
  remote publication or DOI creation.
- [ ] Keep OCFL and graph/vector work deferred until the corpus/workload gate
  in `conductor/tracks.md` is met.
