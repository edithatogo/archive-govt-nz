# Specification: Corrective Legislation Corpus Consolidation

## 1. Corrective Architecture

```mermaid
flowchart TD
    subgraph DonorSource["Donor Repo: corpus-legislation-nz (749918c)"]
        D_API["API Client (nz_api.py)"]
        D_NORM["XML/HTML Normaliser (normalize.py)"]
        D_SHARDS["68 Historical Batches (period_shards.py)"]
        D_PARQUET["Parquet Writer (parquet_writer.py)"]
    end

    subgraph TargetIntegration["Canonical Core: archive-govt-nz"]
        T_ADAPTER["NZLegislationAdapter (adapters/nz_legislation.py)"]
        T_DOMAIN["Legislation Domain (domains/legislation/)"]
        T_CAS["Content-Addressed Storage (Dual SHA-256/BLAKE3)"]
        T_PROV["W3C PROV-O Ledger"]
        T_CLI["CLI & MCP Real Executors"]
        T_HARVEST["Multi-Source Scheduled Harvest"]
    end

    subgraph ExternalDistribution["Publication & Distribution"]
        HF_LIVE["Hugging Face (corpus-legislation-nz)"]
        ZENODO["Zenodo Concept DOI (10.5281/zenodo.20592540)"]
    end

    D_API --> T_ADAPTER
    D_NORM --> T_DOMAIN
    D_SHARDS --> T_DOMAIN
    D_PARQUET --> T_DOMAIN

    T_ADAPTER --> T_CAS
    T_DOMAIN --> T_CAS
    T_DOMAIN --> T_PROV
    T_DOMAIN --> T_CLI
    T_DOMAIN --> T_HARVEST

    T_HARVEST --> HF_LIVE
    T_HARVEST --> ZENODO
```

---

## 2. Legislation Domain Modular Architecture

```
src/archive_govt_nz/domains/legislation/
├── __init__.py          # Public exports
├── api.py               # Robust official API client with retry, backoff & ETags
├── discovery.py         # Work ID discovery, search filtering & scope bounds
├── identity.py          # FRBR Work, Expression, Manifestation & Versioning models
├── models.py            # Typed dataclasses for Acts, Bills, Regs, Provisions & Schedules
├── normalise.py         # Safe ElementTree XML/HTML parser (no regex stripping)
├── validate.py          # Schema validation & integrity assertion rules
├── manifest.py          # Source & transformation manifest compilation
├── coverage.py          # Evidence-backed completeness, gap analysis & audit reporting
├── changes.py           # Feed polling, ETag caching & change detection
├── checkpoints.py       # Resumable checkpointing & period-shard state persistence
├── bootstrap.py         # 68-batch merge, review & verification pipeline
├── corpus.py            # Columnar Snappy Parquet table compilation & JSONL streaming
└── publication.py       # Hugging Face & Zenodo package preparation & verification
```
