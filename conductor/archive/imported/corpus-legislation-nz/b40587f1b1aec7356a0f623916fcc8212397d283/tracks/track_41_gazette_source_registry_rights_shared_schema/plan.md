# Plan - Gazette Source Registry, Rights, And Shared Schema

## Phase 1 - Source Registry And Rights Boundary

- [ ] Task: Create the Gazette source registry.
    - [ ] Define source IDs, source tiers, base URLs, expected artifacts, and
      canonical eligibility.
    - [ ] Record rights, licence, robots/access, and operational caveats for
      each source.
- [ ] Task: Define source retrieval limits.
    - [ ] Set conservative request pacing and bounded smoke-run rules.
    - [ ] State that stealth scraping and access-control bypass are not
      permitted archive mechanisms.
- [ ] Task: Define the source coverage matrix.
    - [ ] Track coverage by source ID, year, issue ID, notice ID, page range,
      and artifact type.
    - [ ] Define gap, overlap, partial-coverage, and blocked-source states.
- [ ] Task: Conductor - User Manual Verification 'Source Registry And Rights Boundary' (Protocol in workflow.md)

## Phase 2 - Shared Schemas

- [ ] Task: Define the raw source archive schema.
    - [ ] Require stable ID, source URL, retrieval method, timestamp, hash,
      artifact path, rights note, and source-local identifiers.
    - [ ] Include HTTP metadata where available.
    - [ ] Include web-archive-quality capture fields where practical.
- [ ] Task: Define the canonical Gazette schema.
    - [ ] Require canonical source, supporting sources, conflicts, confidence,
      normalization version, and provenance links.
    - [ ] Allow historical-only records only when source-tier and rights caveats
      are explicit.
- [ ] Task: Conductor - User Manual Verification 'Shared Schemas' (Protocol in workflow.md)

## Phase 3 - Validation Contract

- [ ] Task: Add schema validation tests.
    - [ ] Cover complete raw source records and canonical records.
    - [ ] Cover missing provenance, missing rights, unstable IDs, and conflict
      fields.
    - [ ] Cover coverage-matrix gap and overlap reporting.
- [ ] Task: Document the implementation contract for Tracks 42-47.
    - [ ] Explain that raw archives remain independent evidence layers.
    - [ ] Explain that canonical records are derived and reproducible.
- [ ] Task: Conductor - User Manual Verification 'Validation Contract' (Protocol in workflow.md)
