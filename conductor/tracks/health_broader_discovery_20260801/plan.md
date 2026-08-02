# Implementation Plan

1. Register the track and parent/nested GitHub issue hierarchy.
2. Freeze query, facet, pagination, response, and redaction policy.
3. Implement typed CKAN metadata discovery using bounded HTTPS requests.
4. Add normalized dataset/organisation/resource candidate records and stable
   deduplication.
5. Add relevance, rights, sensitivity, and ambiguity classifications.
6. Add schema-validated JSON/Markdown manifests and evidence receipts.
7. Add property-based, contract, metamorphic, and deterministic-simulation
   tests, including interrupted and repeated discovery.
8. Run clean-environment validation and review evidence.
9. Hand eligible candidates to a separately approved capture track; do not
   capture or publish from this track.

## Transport compatibility remediation

- [ ] Add bounded GET fallback after POST JSON failure.
- [ ] Record method, parameter variant, page size, status, and response hash.
- [ ] Reconcile GET and POST IDs/counts before accepting a fallback result.
- [ ] Add contract and metamorphic tests for transport equivalence.
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

Contingencies:

1. If GET succeeds and normalized IDs/counts match POST probes, retain both
   receipts and use GET for the affected scope.
2. If GET succeeds but results differ, retain both as a drift conflict and
   remain `unavailable`.
3. If both fail, retain the bounded diagnostic receipt and continue scheduled
   monitoring without capture or publication.
