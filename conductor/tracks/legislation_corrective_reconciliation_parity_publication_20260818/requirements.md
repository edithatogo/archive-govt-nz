# Requirements: Publication Identity Verification and Read-Only Remote Readback

Track: `legislation_corrective_reconciliation_parity_publication_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issues: [#139](https://github.com/edithatogo/archive-govt-nz/issues/139), [#140](https://github.com/edithatogo/archive-govt-nz/issues/140)

## MoSCoW Requirements

### Must
1. **Remote Hugging Face Read-Only Verification**:
   - Query and record live state for:
     - `edithatogo/corpus-legislation-nz`
     - `edithatogo/corpus-legislation-nz-historical`
     - `edithatogo/nz-legislation-corpus`
   - Record exact revision SHAs, files list, sizes, hashes/immutable identifiers, configs, viewer states, dataset card tags, rights, and repository linkage.
2. **Remote Zenodo DOI Resolution & Lineage Audit**:
   - Resolve DOI `10.5281/zenodo.20592540` via official API.
   - Record whether it is a version DOI, corresponding concept DOI (`10.5281/zenodo.20592539`), all public versions, record IDs, files, checksums, metadata, and linked relationships (`isSupplementTo` Hugging Face datasets).
3. **Honest Read-Only Evidence Receipt**:
   - Generate `evidence/migrations/corpus-legislation-nz/remote-publication-readback-receipt.json` capturing request URLs, retrieval timestamps, response SHA-256 hashes, explicit mismatches, and unresolved claims.
   - Prohibit claiming local registry or README text as remote proof.
4. **Anti-Simulation Invariants**:
   - Zero mocked responses represented as live readback.
   - Zero remote write side-effects during readback.
   - Return explicit non-zero or `BLOCKED_REMOTE_READBACK` outcome on network failure.
