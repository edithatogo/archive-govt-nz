# Plan: Publication Identity Verification and Read-Only Remote Readback

1. **Phase 1: Publication Readback Verifier Engine**
   - Implement `tools/verify_public_publication_identities.py` querying live endpoints with request URL capture, timestamp tracking, and SHA-256 payload hashing.
2. **Phase 2: Remote Hugging Face & Zenodo Audit**
   - Verify 3 HF datasets (`edithatogo/corpus-legislation-nz`, `edithatogo/corpus-legislation-nz-historical`, `edithatogo/nz-legislation-corpus`) and Zenodo DOI `10.5281/zenodo.20592540`.
3. **Phase 3: Receipt Generation and Assurance Testing**
   - Implement unit and mocked negative-control tests in `tests/publication/test_verify_public_publication_identities.py`.
   - Run 19-stage assurance check (`tools/check.py`) and emit verified receipt to `evidence/migrations/corpus-legislation-nz/remote-publication-readback-receipt.json`.
> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22. Gated external blockers remain: write token deployment (human authority) and 67 historical batch accounting.
