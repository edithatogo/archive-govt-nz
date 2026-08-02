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
