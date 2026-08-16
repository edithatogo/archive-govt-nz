# Track 7 Plan: Publication and Archive-Distribution Alignment

## Phases

### Phase 1: Publication Models & Receipts Engine
- [x] Implement `ArchivePacket` and `PublicationReceipt` models.
- [x] Implement checksum pinning and remote fixity verification logic.

### Phase 1: Multi-Target Distribution Publisher
- [x] Implement `DistributionPublisher` supporting Hugging Face, Zenodo, and GitHub Releases.
- [x] Standardize `PublicationReceipt` generation and bundle hashing.

### Phase 2: Open Metadata Generators
- [x] Implement Croissant JSON-LD generator in `src/archive_govt_nz/distribution/metadata.py`.
- [x] Implement RO-Crate 1.1 and DCAT-AP 3.0 metadata graphs.

### Phase 3: Dry-Run Verification & Quality Gates
- [x] Implement multi-target `publish_dry_run` with deterministic zip compression.
- [x] Run full 18-stage assurance check suite.
