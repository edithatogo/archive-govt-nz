# Specification: Open Social Data & RIOPA Interoperability Substrate

- **Track ID:** `open_social_riopa_substrate_20260823`
- **Donor / Upstream:** `edithatogo/open_social_data and RIOPA public-data tooling`
- **Treatment:** `Shared archival/publication infrastructure for public social datasets`

---

## 1. Context & Objectives
Integrate open social media capture pipelines and RIOPA archive export receipts into the shared preservation engine.

### Key Reusable Components
- Bluesky/Threads/X/YouTube capture pipelines, RIOPA archive export receipts, CAS media storage

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
