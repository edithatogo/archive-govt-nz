# Mandatory Pre-Acquisition Discovery: Legislation & Gazette Corpus

**Evaluation Date**: 18 August 2026  
**Donor Repository**: `edithatogo/corpus-legislation-nz` (`749918c`)  
**Decision**: **REUSE, VERIFY, AND RESUME (NO BULK RE-DOWNLOAD)**

---

## 1. Discovery Audit

An exhaustive search across local stores, Git histories, Hugging Face, and Zenodo established the following:

1. **Hugging Face Datasets**:
   - Living Dataset: [`edithatogo/corpus-legislation-nz`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz) (active, versioned).
   - Historical Dataset: [`edithatogo/corpus-legislation-nz-historical`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical).
   - Legacy Compatibility Dataset: `edithatogo/nz-legislation-corpus`.
2. **Zenodo Release Lineage**:
   - Concept DOI: `10.5281/zenodo.20592539`.
   - Immutable 2026 version DOI: `10.5281/zenodo.20592540`.
   - Records annual immutable corpus dumps and XML fixity trees.
3. **Historical Batch Manifests**:
   - 68 historical period-sharded batch checkpoints exist covering 33,693 search-derived work identifiers.
4. **Acquisition Decision**:
   - **Reuse**: The existing 33,693 seed inventory and 68 historical batches are verified and reused.
   - **Do Not Re-Download**: No redundant bulk download from the official Legislation API will be executed.
   - **Incremental Sync**: Future continuous synchronization is handled by the canonical `archive-govt-nz` engine.
