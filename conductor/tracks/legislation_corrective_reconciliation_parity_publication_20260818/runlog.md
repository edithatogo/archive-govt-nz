# Run Log: Publication Identity Verification and Read-Only Remote Readback

- Implemented read-only verification harness in `tools/verify_public_publication_identities.py`.
- Queried live Hugging Face datasets:
  - `edithatogo/corpus-legislation-nz` (revision `1efa35e72c378068cfb112d060bd0502497f61b1`, 112 files)
  - `edithatogo/corpus-legislation-nz-historical` (revision `ea9e66fb89c3230fc478f7c6f05f1a82f4fa1174`, 6,788 files, viewer active)
  - `edithatogo/nz-legislation-corpus` (revision `1dea0c678b419a9c16fe7e363488f91d293391d3`, 20 files)
- Resolved Zenodo DOI `10.5281/zenodo.20592540`:
  - Verified version DOI linked to concept DOI `10.5281/zenodo.20592539` (concept record ID `20592539`).
  - Extracted 3 files with MD5 fixity checksums (`nz-legislation-corpus-2026.SHA256SUMS.txt`, `nz-legislation-corpus-2026.tar.zst`, `nz-legislation-corpus-2026.manifest.json`).
  - Extracted linked relationship `isSupplementTo` Hugging Face dataset.
- Generated `evidence/migrations/corpus-legislation-nz/remote-publication-readback-receipt.json` with SHA-256 payload hashes and request timestamps.
- Implemented unit and negative-control test suite in `tests/publication/test_verify_public_publication_identities.py`.
- Passed full 19-stage assurance gate (`tools/check.py`).
- **2026-08-22**: Gated blocker resolved. `HF_TOKEN` and `ZENODO_TOKEN` deployed as GitHub Actions secrets via user action. Wired into `scheduled-legislation-harvest.yml`, `monthly-legislation-reconciliation.yml`, and `quarterly-legislation-recovery.yml`.
