# Track 7 Plan: Publication and Archive-Distribution Alignment

## Phases

### Phase 1: Publication Models & Receipts Engine
- [ ] Implement `ArchivePacket` and `PublicationReceipt` models.
- [ ] Implement checksum pinning and remote fixity verification logic.

### Phase 2: Platform Adapters (Hugging Face, Zenodo, OSF)
- [ ] Refactor `huggingface_publisher.py` to handle both tabular and social-media archive datasets.
- [ ] Implement `zenodo.py` multi-concept deposition publisher.
- [ ] Draft OSF mirror connector.

### Phase 3: Metadata & Derivative Enrichment
- [ ] Integrate DCAT-AP 3.0 and Croissant schema builders.
- [ ] Run full 18-stage assurance check.
