# Plan - NZLII Gazette Redundancy Archive

## Phase 1 - Access And Coverage Decision

- [ ] Task: Probe NZLII Gazette availability safely.
    - [ ] Check robots/access behavior for candidate Gazette URL patterns.
    - [ ] Record coverage, rights, and access evidence.
- [ ] Task: Define NZLII source-state outcomes.
    - [ ] Support usable, partially usable, blocked, and unavailable states.
    - [ ] Define revisit criteria for blocked or unavailable states.
- [ ] Task: Conductor - User Manual Verification 'Access And Coverage Decision' (Protocol in workflow.md)

## Phase 2 - Source Archive Or Blocked Evidence

- [ ] Task: Add tests for NZLII source-state handling.
    - [ ] Cover usable sample archive output.
    - [ ] Cover blocked/unavailable source evidence.
- [ ] Task: Implement the chosen NZLII path.
    - [ ] If usable, archive raw artifacts and normalized records separately.
    - [ ] If blocked, write source-state evidence and skip harvesting.
- [ ] Task: Conductor - User Manual Verification 'Source Archive Or Blocked Evidence' (Protocol in workflow.md)

## Phase 3 - Review And Documentation

- [ ] Task: Add NZLII review checks.
    - [ ] Fail on missing source-state evidence, rights notes, hashes, or
      provenance.
    - [ ] Report NZLII records as secondary-source evidence.
- [ ] Task: Document NZLII role.
    - [ ] Explain access decision, source status, and comparison use.
    - [ ] State that NZLII is not the default canonical source.
- [ ] Task: Conductor - User Manual Verification 'Review And Documentation' (Protocol in workflow.md)
