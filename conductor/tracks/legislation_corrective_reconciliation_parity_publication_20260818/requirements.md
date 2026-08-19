# Requirements: Historical Reconciliation, Parity, and Publication Identity

Track: `legislation_corrective_reconciliation_parity_publication_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`

## Objective
Establish deterministic differential parity between historical donor batches (`edithatogo/corpus-legislation-nz`) and canonical target preservation (`archive-govt-nz`), and enforce cryptographically verifiable publication identity without simulated remote state.

## MoSCoW Requirements

### Must
1. **Multi-Batch Historical Inventory Accounting**:
   - Reconcile all 68 historical donor batches individually without conflating them into a single aggregate batch.
   - Bind every historical batch to its distinct `batch_id`, timestamp, CAS root hash, and record manifest.

2. **Differential Parity & Fixity Harness**:
   - Execute bitstream SHA-256 and semantic derivative matching against donor raw payloads via `tools/generate_executable_legislation_parity.py`.
   - Record exact match counts, missing item counts, digest mismatches, and structural differences.

3. **External Publication Identity Preservation**:
   - Retain Hugging Face dataset identifier `edithatogo/corpus-legislation-nz` and concept DOI `10.5281/zenodo.20592540`.
   - Maintain publication metadata descriptors under `registry/publications/legislation.yml`.

4. **Hosted Readback Token & Environment Gating**:
   - Require structured readback receipt (`evidence/migrations/corpus-legislation-nz/hosted-publication-readback.json`) containing `verified_revision` and remote cryptographic token.
   - When remote credentials (`HF_TOKEN`, `ZENODO_TOKEN`) are absent, honestly report gated status rather than creating fabricated success receipts.

### Must Not (Anti-Simulation)
1. Must not fabricate remote upload receipts or pretend an offline run uploaded data to Hugging Face or Zenodo.
2. Must not hardcode 100% parity or mock zero mismatches without executing comparison against real historical payloads.
3. Must not mutate historical batch timestamps or collapse multi-batch histories.
