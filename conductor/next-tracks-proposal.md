# Next Tracks Proposal

**Date:** 2026-08-22
**Status:** Proposal

## Overview

All approved tracks are now complete. The following tracks are proposed for the next implementation phase, prioritized by roadmap alignment and dependency order.

---

## Track A: NZ Gazette Integration and Archive Workflow

**Rationale:** The corrective programme Child Track 12 (Gazette residual) was explicitly "kept separate and incomplete." Three donor issues (#142, #143, #144) track Gazette freshness, workflow, and cross-source comparison. The Gazette source-set is already configured (`config/source-sets/nz-gazette.yml`) and the adapter exists (`src/archive_govt_nz/adapters/nz_gazette.py`).

**Proposed ID:** `nz_gazette_archive_workflow_20260822`

**Type:** feature

**MoSCoW Requirements:**
- Must: Implement Gazette archive workflow with scheduled capture
- Must: Wire Gazette source-set to weekly harvest schedule
- Must: Produce parity evidence against existing Gazette fixtures
- Should: Implement Gazette freshness and change detection
- Should: Cross-source compare Official & DigitalNZ Gazette sources
- Could: Build Gazette-specific corpus and publication package
- Won't: Include Victoria/LexisNexis historical Gazette (deferred)

**Phases:**
1. Phase 1: Audit existing Gazette adapter and source-set configuration
2. Phase 2: Implement Gazette harvest orchestrator
3. Phase 3: Add scheduled Gazette workflow to CI
4. Phase 4: Parity and publication verification
5. Phase 5: 19-stage assurance gate

---

## Track B: Quality Frontier — Testing, CI/CD & Security Hardening

**Rationale:** Three donor issues (#158, #159, #160) target quality frontier improvements. As the project grows, testing and CI/CD gaps need closing.

**Proposed ID:** `quality_frontier_hardening_20260822`

**Type:** quality

**MoSCoW Requirements:**
- Must: Close warranted testing gaps identified in the corrective programme
- Must: Maximize security and solo-maintainer context automation
- Must: Complete evidence-based repository hardening
- Should: Add additional mutation testing lanes
- Should: Implement automated dependency health reporting
- Could: Add fuzz testing for critical parsers
- Won't: Introduce fictional second-person review gates

**Phases:**
1. Phase 1: Audit current testing and CI/CD gaps
2. Phase 2: Implement missing test coverage
3. Phase 3: Security hardening and supply-chain controls
4. Phase 4: Evidence-based repository hardening
5. Phase 5: Full assurance gate

---

## Track C: Health Payload Capture Activation

**Rationale:** Track 14 (health_payload_capture) is complete with zero payloads admitted — all 158 resources were decision-required. Now that credentials are deployed and the broader health discovery is stable, resource-level rights can be re-evaluated.

**Proposed ID:** `health_payload_activation_20260822`

**Type:** feature

**MoSCoW Requirements:**
- Must: Re-evaluate resource-level rights for Ministry of Health resources
- Must: Classify eligible resources for payload capture
- Must: Implement bounded retrieval for newly eligible resources
- Should: Produce WARC and Parquet derivatives for captured payloads
- Should: Verify captured payloads against published HF dataset
- Could: Add health-specific publication package
- Won't: Capture without explicit resource-level eligibility receipt

**Phases:**
1. Phase 1: Re-evaluate 158 resource rights classifications
2. Phase 2: Implement capture for newly eligible resources
3. Phase 3: Derivative generation and validation
4. Phase 4: Publication preparation (prepared-not-published)
5. Phase 5: Full assurance gate

---

## Track D: Dataset Identifier Interlinking

**Rationale:** Donor issue #149 tracks cross-referencing identifiers across legislation datasets. This is active corrective work that maps to the target.

**Proposed ID:** `dataset_identifier_interlinking_20260822`

**Type:** corrective

**MoSCoW Requirements:**
- Must: Cross-reference work IDs across legislation, Gazette, and other datasets
- Must: Produce a stable identifier mapping manifest
- Should: Verify identifier consistency against published HF datasets
- Should: Add identifier validation to the CI pipeline
- Could: Expose identifier relationships via CLI/MCP
- Won't: Modify upstream identifiers or create new identifier schemes

**Phases:**
1. Phase 1: Audit current identifier landscape
2. Phase 2: Build identifier mapping and cross-reference tooling
3. Phase 3: Validate against published datasets
4. Phase 4: CI integration and evidence generation
5. Phase 5: Full assurance gate

---

## Priority Recommendation

1. **Track A (Gazette)** — Highest priority; completes the final gap from the corrective programme
2. **Track B (Quality Frontier)** — Foundation for all subsequent tracks
3. **Track C (Health Payload)** — Unlocks value from the completed health discovery
4. **Track D (Identifier Interlinking)** — Enables cross-dataset queries

## Deferred (not proposed)

- **Graph/vector indexing** — Blocked by deferral gate (see `evidence/deferral-gate-assessment.md`)
- **RO-Crate/BagIt/OCFL conformance** — Blocked by deferral gate
- **Preservation format adoption** — Blocked by deferral gate