# Requirements (MoSCoW)

## Must

- M-01: Evaluate each format using identical deterministic fixtures.
- M-02: Record tool versions, commands, hashes, results, and limitations.
- M-03: Verify package integrity and provenance links without mutating source objects.
- M-04: Fail closed when a validator is unavailable or a required assertion fails.

## Should

- S-01: Produce paired Markdown and JSON evidence.
- S-02: Test round-trip extraction and checksum closure.
- S-03: Compare operational cost, portability, and suitability for HF/Zenodo.

## Could

- C-01: Add independent validators and cross-platform runs.
- C-02: Evaluate a larger representative corpus after the fixture gate passes.

## Won't (this track)

- W-01: Claim full conformance based on self-generated fixtures.
- W-02: Replace the current content-addressed store or create a Zenodo release.
- W-03: Make OCFL mandatory without production-corpus evidence.
