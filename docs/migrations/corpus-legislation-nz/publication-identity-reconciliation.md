# External Publication Identity Reconciliation: Legislation & Gazette

**Evaluation Date**: 18 August 2026

---

## 1. Identity Continuity Table

| Identity Class | Target Identifier | Previous Authority | Canonical New Authority | Treatment |
|---|---|---|---|---|
| **Hugging Face Living Dataset** | [`edithatogo/corpus-legislation-nz`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz) | `corpus-legislation-nz` | `edithatogo/archive-govt-nz` | **Preserved**. Living dataset continuous sync. |
| **Hugging Face Historical Archive** | [`edithatogo/corpus-legislation-nz-historical`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical) | `corpus-legislation-nz` | `edithatogo/archive-govt-nz` | **Preserved**. Historical period-sharded batches. |
| **Zenodo Concept DOI** | [`10.5281/zenodo.20592539`](https://doi.org/10.5281/zenodo.20592539) | `corpus-legislation-nz` | `edithatogo/archive-govt-nz` | **Preserved Concept Lineage**. The immutable 2026 release remains version DOI [`10.5281/zenodo.20592540`](https://doi.org/10.5281/zenodo.20592540). |
| **NPM Package / Standalone CLI** | `nz-legislation-tool` (`nzlegislation`) | `legislation` | `edithatogo/legislation` | **Retained Standalone**. Explicit non-donor boundary. |

---

## 2. Provenance and Metadata Alignment

All Hugging Face dataset cards, Zenodo deposit records, and RO-Crate/Croissant descriptors are updated to reference `edithatogo/archive-govt-nz` as the publishing authority while preserving all historical contributors, original URLs, and Crown Copyright licenses.
