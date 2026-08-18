# Programme Specification: Legislation Corpus Consolidation

## 1. Current Donor Architecture (`corpus-legislation-nz`)

```mermaid
flowchart TD
    subgraph Donor["corpus-legislation-nz (Historical)"]
        SOAP["NZ Legislation Web Service / RSS"]
        SCRIPTS["Ad-hoc Python Scripts (scripts/fetch_*.py)"]
        BATCH["68 Historical Period Batches"]
        RAW["raw_xml/ & raw_html/"]
        JSONL["JSONL / Parquet Exporters"]
        HF_PUB["scripts/publish_hf.py"]
        ZEN_PUB["scripts/publish_zenodo.py"]
    end

    SOAP --> SCRIPTS
    SCRIPTS --> RAW
    RAW --> BATCH
    BATCH --> JSONL
    JSONL --> HF_PUB
    JSONL --> ZEN_PUB
```

---

## 2. Target Architecture (`archive-govt-nz`)

```mermaid
flowchart TD
    subgraph Ingestion["Unified Source Adapters"]
        LEG_ADAPTER["NZLegislationAdapter (adapters/nz_legislation.py)"]
        GAZ_ADAPTER["NZGazetteAdapter (adapters/nz_gazette.py)"]
    end

    subgraph Core["Canonical Preservation Core"]
        CAS["Content-Addressed Store (SHA-256 / BLAKE3)"]
        PROV["W3C PROV-O Ledger"]
        WARC["ISO 28500 Compactor"]
        DOMAIN["Legislation Domain Normaliser & Validator"]
    end

    subgraph Derivatives["Analytical & Distribution Tier"]
        PARQUET["Parquet Columnar Corpus"]
        JSONL_CORP["JSONL Stream Corpus"]
        RO_CRATE["RO-Crate 1.1 & Croissant Descriptors"]
        HF_DEST["Hugging Face (corpus-legislation-nz)"]
        ZEN_DEST["Zenodo Concept 10.5281/zenodo.20592540"]
    end

    Ingestion --> Core
    Core --> Derivatives
```

---

## 3. Migration Stages

```mermaid
sequenceDiagram
    participant Baseline as Baseline Audit & Discovery
    participant Domain as Target Domain & Adapters
    participant Parity as Differential Parity & Replay
    participant Cutover as Publication Cutover
    participant Closeout as Donor Archival & Closeout

    Baseline->>Domain: Reconciled Schemas & Seed Registries
    Domain->>Parity: Ingest Historical Batches & Verify Fixity
    Parity->>Cutover: Verified Parity Receipts & Staging Packages
    Cutover->>Closeout: Redirect Notice & Immutable Tag
```

---

## 4. Legal Document Identity & Versioning Model

```mermaid
classDiagram
    class LegislationWork {
        +str work_id
        +str title
        +str legislation_type
        +str canonical_uri
    }
    class LegislationExpression {
        +str expression_id
        +str version_label
        +datetime in_force_start
        +datetime in_force_end
        +str status
    }
    class LegislationManifestation {
        +str manifestation_id
        +str mime_type
        +str raw_cas_hash_sha256
        +str raw_cas_hash_blake3
        +int byte_size
    }
    class NormalisedCorpusRecord {
        +str document_id
        +dict front_matter
        +list sections
        +list schedules
        +str plain_text
    }

    LegislationWork "1" *-- "many" LegislationExpression
    LegislationExpression "1" *-- "many" LegislationManifestation
    LegislationManifestation --> NormalisedCorpusRecord : Normalises to
```

---

## 5. Publication Graph

```mermaid
flowchart LR
    PACKAGE["Legislation Package (JSONL / Parquet / WARC)"]
    RIGHTS["Crown Copyright Open Gate"]
    PLAN["Publication Plan & Manifest"]
    HF_LIVE["HF: edithatogo/corpus-legislation-nz"]
    HF_HIST["HF: edithatogo/corpus-legislation-nz-historical"]
    ZENODO["Zenodo Concept DOI 10.5281/zenodo.20592540"]

    PACKAGE --> RIGHTS
    RIGHTS --> PLAN
    PLAN --> HF_LIVE
    PLAN --> HF_HIST
    PLAN --> ZENODO
```

---

## 6. Rollback Path

```mermaid
flowchart TD
    START["Rollback Trigger Detected"]
    FREEZE["Revert Target Schedules to Previous Checkpoint"]
    RESTORE["Restore Canonical State from Baseline Checkpoint"]
    REPLAY["Re-run Deterministic Replay Drill"]
    REPORTS["Emit Rollback Incident Receipt"]

    START --> FREEZE
    FREEZE --> RESTORE
    RESTORE --> REPLAY
    REPLAY --> REPORTS
```
