# Architecture Specification: New Zealand Gazette Archival Engine

**Scope**: Official government notices, proclamations, regulations, and departmental orders.

---

## 1. Multi-Source Ingestion Pipeline

1. **Official Gazette Portal**: Real-time polling of weekly issues and individual notice feeds.
2. **DigitalNZ Integration**: Historical back-issue ingestion (1840–1992).
3. **NZLII Redundancy**: Cross-validation against open-access legal redundancy archives.

---

## 2. Canonical Reconciliation

The Gazette domain module merges multi-source notices into unified `GazetteRecord` entities with strict provenance tracking, deduplicating notices while preserving format-specific artifacts in CAS.
