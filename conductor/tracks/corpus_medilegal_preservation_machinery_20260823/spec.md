# Specification: Medico-Legal Case Law Preservation Machinery

- **Track ID:** `corpus_medilegal_preservation_machinery_20260823`
- **Donor / Upstream:** `edithatogo/corpus-cases-medilegal-nz`
- **Treatment:** `Shared preservation/publication machinery assimilation; corpus remains independently versioned`

---

## 1. Context & Objectives
Assimilate case law and tribunal decision preservation machinery into archive-govt-nz while preserving independent case corpus identity.

### Key Reusable Components
- Judgment/decision citation graphs, anonymization verification gates, tribunal record normalizers

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
