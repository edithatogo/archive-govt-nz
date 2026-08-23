# Specification: FYI (OIA) Archive Substrate Federation

- **Track ID:** `fyi_archive_substrate_federation_20260823`
- **Donor / Upstream:** `edithatogo/fyi-archive`
- **Treatment:** `Shared archive/publication substrate; federated integration (excluding fyi-cli / foi-o)`

---

## 1. Context & Objectives
Establish shared preservation and CAS attachment indexing substrate for OIA correspondence, keeping fyi-archive federated.

### Key Reusable Components
- OIA request/attachment metadata, correspondence thread models, agency authority linkages

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
