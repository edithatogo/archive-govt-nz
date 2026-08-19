# Review: Historical Reconciliation, Parity, and Publication Identity

## Status: IN_PROGRESS (Remote Publication Gated)

### Verified Invariants
- 68 historical donor batches reconciled with CAS root hashes.
- Differential parity harness executes 4 verification lanes with zero fabrication.
- Publication package staging validates parquet and JSONL derivative integrity.
- External dataset identities preserved (`edithatogo/corpus-legislation-nz`, concept DOI `10.5281/zenodo.20592540`).

### Gated Preconditions
- Live remote write to Hugging Face and Zenodo remains gated on production deployment tokens (`HF_TOKEN`, `ZENODO_TOKEN`) and operator triggering.
