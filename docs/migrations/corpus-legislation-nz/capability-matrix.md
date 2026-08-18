# Capability Matrix: `corpus-legislation-nz` → `archive-govt-nz`

**Evaluation Date**: 18 August 2026

---

## 1. Reconciled Capabilities & Dispositions

| Capability ID | Capability Name | Donor Location | Target Location | Final Disposition |
|---|---|---|---|---|
| **leg-cap-adapter** | Official Legislation API/RSS Ingestion | `src/corpus_legislation_nz/acquisition/` | [`src/archive_govt_nz/adapters/nz_legislation.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/nz_legislation.py) | `assimilate_as_source_adapter` |
| **leg-cap-domain** | Legislation Normalisation & Versioning | `src/corpus_legislation_nz/core/` | [`src/archive_govt_nz/domains/legislation/`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/domains/legislation/) | `assimilate_as_domain_module` |
| **leg-cap-gazette** | NZ Gazette Notice & Issue Ingestion | `src/corpus_legislation_nz/gazette/` | [`src/archive_govt_nz/adapters/nz_gazette.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/nz_gazette.py) | `assimilate_as_domain_module` |
| **leg-cap-cas-storage** | Content-Addressed Storage (CAS) | `src/corpus_legislation_nz/storage/` | [`src/archive_govt_nz/object_store.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/object_store.py) | `assimilate_into_core` |
| **leg-cap-corpus-parquet** | Parquet & JSONL Corpus Generation | `src/corpus_legislation_nz/export/` | [`src/archive_govt_nz/domains/legislation/corpus.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/domains/legislation/corpus.py) | `assimilate_as_domain_module` |
| **leg-cap-hf-publication** | Hugging Face Dataset Publisher | `scripts/publish_hf.py` | [`src/archive_govt_nz/distribution/publisher.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/distribution/publisher.py) | `assimilate_into_core` |
| **leg-cap-zenodo-doi** | Zenodo Immutable Snapshots & DOI | `scripts/publish_zenodo.py` | [`src/archive_govt_nz/zenodo.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/zenodo.py) | `preserve_as_external_identity` |
| **leg-cap-cli-compat** | CLI `nzlc` Deprecation Shim | `src/corpus_legislation_nz/cli.py` | [`src/archive_govt_nz/cli_compat.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/cli_compat.py) | `preserve_as_compatibility_interface` |
| **leg-cap-interactive-search** | Interactive CLI / Citation Tool | `edithatogo/legislation` | Standalone repo (`legislation`) | `federate_with_standalone_product` |
| **leg-cap-experimental-nlp** | Exploratory Embeddings & NLP | `experiments/` | N/A | `deliberately_retire` |
