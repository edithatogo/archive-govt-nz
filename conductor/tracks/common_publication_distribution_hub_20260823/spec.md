# Specification: Common Multi-Platform Publication & Distribution Hub

- **Track ID:** `common_publication_distribution_hub_20260823`
- **Donor / Upstream:** `Common multi-target publishing architecture`
- **Treatment:** `Unified distribution engine for Hugging Face, Zenodo, OSF, and GitHub Releases`

---

## 1. Context & Objectives
Build unified, evidence-gated multi-target publication engine supporting Hugging Face, Zenodo, OSF, and GitHub Releases.

### Key Reusable Components
- RO-Crate 1.1, Croissant JSON-LD, checksum signing, remote readback verifiers

---

## 2. Architecture & Data Flow
1. **Bronze Acquisition:** Raw payload preservation in CAS and snapshot manifests.
2. **Silver Normalization:** Typed Polars/PyArrow Parquet schemas conforming to domain contracts.
3. **Gold Derivatives & Interlinks:** DuckDB views, entity interlinking, and RO-Crate 1.1 / Croissant metadata.
4. **Common Distribution:** Integrated with the common publication adapters (Hugging Face, Zenodo, OSF, GitHub Releases).
