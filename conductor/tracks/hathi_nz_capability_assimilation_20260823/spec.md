# Specification: HathiTrust NZ Historic Corpus Capability Assimilation

- **Track ID:** `hathi_nz_capability_assimilation_20260823`
- **Donor / Upstream:** `edithatogo/hathi-nz`
- **Treatment:** `Selective capability assimilation with strict source-rights boundary preservation`

---

## 1. Context & Objectives
Assimilate historic NZ text preservation capabilities from hathi-nz, preserving source-rights classification and OCR text fixity.

### Key Reusable Components
- Volume/page metadata parsers, OCR text normalizers, rights classification logic

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
