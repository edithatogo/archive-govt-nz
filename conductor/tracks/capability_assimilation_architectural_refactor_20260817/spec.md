# Track 11 Specification: Capability Assimilation and Architectural Refactor

## Purpose
Refactor assimilated capabilities into the unified shared core, eliminating legacy wrappers, duplicate network logic, and technical debt, raising all migrated code to the target repository's strict engineering standard.

## Context & Objectives
1. Eliminate duplicate retry, backoff, jitter, logging, and configuration abstractions.
2. Transplant donor's comprehensive `registry/` into `src/archive_govt_nz/core/registry.py`.
3. Normalize all source adapters onto `AsyncBaseCaptureAdapter` and ensure all write through streaming SHA-256 CAS.
4. Elevate all donor-derived code to pass all 18 quality gates with >95% branch coverage.

## Deliverables
- Cleaned and refactored `src/archive_govt_nz/` package tree
- Performance benchmarks and mutation test suites
- Full 18-stage assurance signoff
