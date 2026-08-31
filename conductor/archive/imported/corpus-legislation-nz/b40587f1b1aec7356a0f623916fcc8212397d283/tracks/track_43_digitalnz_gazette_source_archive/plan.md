# Plan - DigitalNZ Gazette Source Archive

## Phase 1 - dnz Integration Contract

- [ ] Task: Validate the local `dnz` CLI path and capabilities.
    - [ ] Confirm `dnz search` can express `primary_collection=New Zealand
      Gazette`.
    - [ ] Decide whether anonymous public API support or `DIGITALNZ_API_KEY`
      is required for regular harvesting.
- [ ] Task: Create or link the `dnz` dependency track.
    - [ ] Track Gazette export mode, deterministic paging, JSONL/page
      manifests, and validation evidence in the `dnz` repo.
    - [ ] Record the `dnz` issue, PR, or track link in this track before
      relying on cross-repo behavior.
- [ ] Task: Define the DigitalNZ source manifest.
    - [ ] Include query parameters, page state, API metadata, timestamps,
      hashes, and output paths.
    - [ ] Align fields with the Track 41 raw source schema.
- [ ] Task: Conductor - User Manual Verification 'dnz Integration Contract' (Protocol in workflow.md)

## Phase 2 - Resumable Export

- [ ] Task: Add tests for DigitalNZ Gazette export planning.
    - [ ] Cover stable query parameters and deterministic page ordering.
    - [ ] Cover resume state and per-page manifest entries.
- [ ] Task: Implement or wire a bounded export wrapper.
    - [ ] Reuse `dnz` for API calls where practical.
    - [ ] Store raw API pages separately from normalized JSONL records.
- [ ] Task: Conductor - User Manual Verification 'Resumable Export' (Protocol in workflow.md)

## Phase 3 - Review And Comparison Readiness

- [ ] Task: Add DigitalNZ source review checks.
    - [ ] Fail on missing rights fields, source URLs, landing URLs, IDs, or
      manifest hashes.
    - [ ] Report metadata-only records separately from text-bearing records.
- [ ] Task: Document DigitalNZ archive use.
    - [ ] Explain `dnz` dependency, credential handling, and source status.
    - [ ] Explain how DigitalNZ corroborates official and historical sources.
- [ ] Task: Conductor - User Manual Verification 'Review And Comparison Readiness' (Protocol in workflow.md)
