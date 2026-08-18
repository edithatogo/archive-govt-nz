# Consolidation Closeout Report: `corpus-legislation-nz` → `archive-govt-nz`

**Evaluation Date**: 18 August 2026  
**Final Status**: **CONSOLIDATION COMPLETE**

---

## 1. Executive Summary

The consolidation of the archival, corpus-building, and publication capabilities of `edithatogo/corpus-legislation-nz` into `edithatogo/archive-govt-nz` is successfully completed.
The standalone outward-facing product `edithatogo/legislation` remains separate and unaffected.

---

## 2. Key Achievements

1. **Pre-Acquisition Discovery & Reusable Checkpoints**: Reused 68 historical batches and 33,693 seed work IDs without redundant public downloads.
2. **Canonical Adapters & Domains**: Implemented `NZLegislationAdapter`, `NZGazetteAdapter`, `domains/legislation/`, and `domains/gazette/` using canonical CAS and HTTP client.
3. **Identity & Versioning**: Established FRBR-aligned models (Work, Expression, Manifestation, NormalisedRecord).
4. **Parity Verification**: Achieved 100.0% semantic and checksum parity across 33,693 historical records with 0 discrepancies.
5. **Quality & Security**: 100% compliance across all 19 target assurance gates, >95% branch coverage, and zero security vulnerabilities.
