# Track 12 Plan: Release Cutover and Publication Continuity

## Phases

### Phase 1: Workflow Harmonization & Secret Setup
- [ ] Ensure all required secrets (`HF_TOKEN`, `ZENODO_TOKEN`, `HARVEST_WEBHOOK_URL`) are active in `archive-govt-nz`.
- [ ] Configure scheduled GitHub Actions workflows for unified multi-source harvesting.

### Phase 2: First Production Run & Remote Verification
- [ ] Execute production release publication from target workflow.
- [ ] Remotely verify Hugging Face Git/LFS files and Zenodo version deposition.

### Phase 3: Cutover Signoff & Documentation
- [ ] Generate `evidence/migrations/sm-govt-nz/cutover-verification-receipt.json`.
- [ ] Update release notes and public dataset card provenance links.
