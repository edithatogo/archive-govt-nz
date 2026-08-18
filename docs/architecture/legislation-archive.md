# Architecture Specification: Legislation Preservation Engine

**Author**: `archive-govt-nz` core team  
**Status**: Canonical Architecture Specification  
**Scope**: Statutory Instruments, Acts, Bills, Regulations, Deemed Regulations

---

## 1. Overview

The legislation preservation engine provides end-to-end bulk discovery, content-addressed storage, document-level normalisation, and multi-format publication of New Zealand legislation.

```
Official Web / API --> NZLegislationAdapter --> CAS Store (SHA-256/BLAKE3) --> Normaliser --> Parquet & JSONL Corpus --> HF / Zenodo / RO-Crate
```

---

## 2. Ingestion & Storage Principles

1. **Immutable Raw Evidence**: All retrieved XML and HTML documents are stored verbatim in Content-Addressed Storage (CAS).
2. **Dual-Hash Integrity**: SHA-256 and BLAKE3 checksums are computed and pinned upon ingestion.
3. **Resumable Sharding**: Batch checkpoints allow distributed, interruptible acquisition without re-fetching identical manifests.
