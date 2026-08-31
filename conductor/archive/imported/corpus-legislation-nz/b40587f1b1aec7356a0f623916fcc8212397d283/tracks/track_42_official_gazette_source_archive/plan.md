# Plan - Official Gazette Source Archive

## Phase 1 - Discovery And Manifest Contract

- [ ] Task: Add official issue discovery tests.
    - [ ] Cover issue listing parsing and canonical no-trailing-slash URL use.
    - [ ] Cover stable issue IDs and deterministic ordering.
- [ ] Task: Define the official source manifest.
    - [ ] Include raw artifact paths, HTTP metadata, hashes, timestamps, and
      source URLs.
    - [ ] Align fields with the Track 41 raw source schema.
- [ ] Task: Conductor - User Manual Verification 'Discovery And Manifest Contract' (Protocol in workflow.md)

## Phase 2 - Retrieval And Extraction

- [ ] Task: Implement bounded issue PDF retrieval.
    - [ ] Support dry-run, resume state, and conservative request pacing.
    - [ ] Store PDFs separately from extracted text.
- [ ] Task: Implement bounded notice-page capture.
    - [ ] Capture only public pages allowed by the source registry.
    - [ ] Store HTML/text extraction with provenance and content hashes.
- [ ] Task: Conductor - User Manual Verification 'Retrieval And Extraction' (Protocol in workflow.md)

## Phase 3 - Review And Documentation

- [ ] Task: Add source archive review checks.
    - [ ] Fail on missing raw artifacts, hashes, provenance, or rights notes.
    - [ ] Report extraction failures separately from retrieval failures.
- [ ] Task: Document official Gazette archive operation.
    - [ ] Include bounded smoke commands and access policy.
    - [ ] Explain canonical-preferred status for official source records.
- [ ] Task: Conductor - User Manual Verification 'Review And Documentation' (Protocol in workflow.md)
