# Evidence: Publication Identity Verification and Read-Only Remote Readback

## Verification Engine & Receipts
- `tools/verify_public_publication_identities.py`
- `evidence/migrations/corpus-legislation-nz/remote-publication-readback-receipt.json` (SHA-256 verified responses, 0 mismatches)
- `contracts/publication/legislation-publication-identity.contract.yaml`
- `registry/publications/legislation.yml`

## Test Suite
- `tests/publication/test_verify_public_publication_identities.py`
- `tests/publication/test_publication.py`
- `tests/publication/test_zenodo_client.py`
