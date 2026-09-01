# Canonical Hugging Face metadata publication gate

This checklist describes one bounded external action. It is not an authorization or a publication receipt.

- [ ] Resolve the Prompt 13 operational-proof prerequisite and record its exact receipt.
- [ ] Obtain accountable approval that names the existing dataset `edithatogo/corpus-legislation-nz`, the candidate manifest SHA-256, the exact files permitted, and whether any payload bytes are permitted. No approval means no upload.
- [ ] Recompute every candidate file hash and require an exact match with `publication-candidate-manifest.json`.
- [ ] Update only the existing canonical identity. Do not create a dataset, change the historical or snapshot identities, mint a DOI, or alter access controls unless separately authorised.
- [ ] After any authorised update, record the returned immutable revision and independently read back the card, `RIGHTS.md`, file inventory, access state, origin commit, state roots, roles, and counts at that revision.
- [ ] Keep the issue incomplete if readback is unavailable, access-controlled, contradictory, or hash-mismatched.
