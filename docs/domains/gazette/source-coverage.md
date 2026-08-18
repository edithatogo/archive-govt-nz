# New Zealand Gazette Source Coverage & Reconciliation

**Evaluation Date**: 18 August 2026

---

## 1. Multi-Source Coverage Tiers

| Source Repository | Temporal Scope | Acquisition Mechanism | Rights Status |
|---|---|---|---|
| **Official NZ Gazette** | 1993 – 2026 | Direct API & Web Ingestion (`adapters/nz_gazette.py`) | Crown Copyright Open |
| **DigitalNZ Gazette Archive** | 1840 – 1992 | Federated dependency (`edithatogo/dnz`) | Open Access Public Domain |
| **NZLII Gazette Redundancy** | 1900 – 2000 | Secondary cross-reference reconciliation | Open Access |

---

## 2. Canonical Reconciliation Strategy

1. Maintain raw XML, PDF, and HTML payloads in content-addressed storage.
2. Build canonical `GazetteRecord` entities with cross-source provenance mapping.
3. Provide annual snapshots versioned in Zenodo and Hugging Face.
