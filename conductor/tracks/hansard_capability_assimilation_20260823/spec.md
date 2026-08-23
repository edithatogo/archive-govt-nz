# Specification: Hansard Corpus Capability Assimilation

- **Track ID:** `hansard_capability_assimilation_20260823`
- **Donor / Upstream:** `edithatogo/corpus-nz-hansard`
- **Treatment:** `Selective capability assimilation into archive_govt_nz/domains/hansard/`

---

## 1. Context & Objectives
Assimilate Hansard preservation and speech extraction pipelines into archive-govt-nz while keeping corpus-nz-hansard separately citable and versioned.

### Key Reusable Components
- Debate XML parsers, MP/Speaker models, parliamentary speech schemas, Parquet builders

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
