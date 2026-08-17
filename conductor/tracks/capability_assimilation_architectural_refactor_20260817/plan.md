# Track 11 Plan: Capability Assimilation and Architectural Refactor

## Phases

### Phase 1: Core Consolidation & Registry Unification
- [x] Implement `src/archive_govt_nz/core/registry.py` with 350+ agency seed fixtures.
- [x] Remove legacy donor utility scripts and ad-hoc logging dependencies.

### Phase 2: Adapter Normalization & Fixity Binding
- [x] Refactor all capture modules onto `AsyncBaseCaptureAdapter`.
- [x] Bind all outputs to SHA-256 CAS and W3C PROV-O ledger events.

### Phase 3: Quality Hardening & Mutation Testing
- [x] Add mutation testing suites for feed, social, and video parsers.
- [x] Verify clean execution across all 18 assurance stages.
