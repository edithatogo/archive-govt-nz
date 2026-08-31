# Plan - Victoria/LexisNexis Historical Gazette Archive

## Phase 1 - Rights And Access Gate

- [ ] Task: Record historical archive rights and access terms.
    - [ ] Capture copyright, licence, robots/access, and source ownership
      notes.
    - [ ] Define allowed retrieval scope and stop conditions.
- [ ] Task: Define historical source identity.
    - [ ] Define stable source IDs for year, issue, page, and notice-like
      records where available.
    - [ ] Define historical-only caveats for canonical comparison.
- [ ] Task: Conductor - User Manual Verification 'Rights And Access Gate' (Protocol in workflow.md)

## Phase 2 - Bounded Historical Archive

- [ ] Task: Add historical discovery tests.
    - [ ] Cover year index parsing and deterministic ordering.
    - [ ] Cover source IDs, page/year references, and rights fields.
- [ ] Task: Implement a bounded sample archive.
    - [ ] Store raw index/content artifacts separately from normalized output.
    - [ ] Write manifests, hashes, and review input files.
- [ ] Task: Conductor - User Manual Verification 'Bounded Historical Archive' (Protocol in workflow.md)

## Phase 3 - Review And Canonical Readiness

- [ ] Task: Add historical source review checks.
    - [ ] Fail on missing rights caveats, source URLs, hashes, or unstable
      source IDs.
    - [ ] Report historical-only candidates separately.
- [ ] Task: Document historical source use.
    - [ ] Explain coverage range, rights caveats, and comparison role.
    - [ ] State that bulk retrieval requires the access gate to pass.
- [ ] Task: Conductor - User Manual Verification 'Review And Canonical Readiness' (Protocol in workflow.md)
