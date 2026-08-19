# Requirements: Reconciliation, Differential Parity Harness, and Publication Continuity

Track: `legislation_corrective_reconciliation_parity_publication_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#139](https://github.com/edithatogo/archive-govt-nz/issues/139), [#140](https://github.com/edithatogo/archive-govt-nz/issues/140)

## MoSCoW Requirements

### Must
1. **Multi-Batch Historical CAS Reconciliation**:
   - Reconcile all 68 historical donor batches (33,693 seed work IDs) deterministically.
2. **Differential Parity Harness**:
   - Differential byte-by-byte and structure parity execution in `tools/generate_executable_legislation_parity.py`.
   - Evidence receipts in `evidence/migrations/corpus-legislation-nz/parity/`.
3. **Publication Continuity & Token Gating**:
   - Preservation of Zenodo concept DOI `10.5281/zenodo.20592540` and Hugging Face dataset identifier `edithatogo/corpus-legislation-nz`.
   - Honest token protection for remote writes.
