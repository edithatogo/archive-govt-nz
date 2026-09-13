# Independent operational artifact verification

The verifier retrieved run, jobs, artifact metadata, and all three ZIP files anew
through GitHub REST API using authenticated read-only `gh api` requests. No
retained local artifact was reused. API response hashes and selected public fields
are retained in hosted-readback.json; no signed download URLs are retained.

The current target verifier `tools/legislation_parent_state.py` executed `unpack`,
`state_roots`, `check_lineage`, and `verify_parent` on the downloaded complete
state. The native `tools/reconcile_one_legislation_batch.py` then ran against the
500-ID governed seed, extracted manifest/checkpoint, and CAS. It reported zero
mismatches and 852 scoped records; full-state verification covered all 904 CAS
objects. The counts refer to different scopes and are not interchangeable.

Additional assertions bound artifact byte counts and SHA-256 digests to API
metadata, run success and software commit to the continuation, all six state roots
to the seal, exact seed IDs to all 500 per-work outcomes, and accounting totals.
The valid-parent check passed; a one-byte CAS mutation was rejected with
`VerificationError object_sha256`. No mutation was written to the real payload.

All verification ran with the Python/environment and target revision recorded in
verification.json. No feature or verifier changed. Full repository validation and
exact-head hosted assurance remain required before the eventual PR merge.

This is preparatory primary-evidence collection, not a Prompt 21 completion claim.
No workflow was dispatched and no external state was mutated. The downloaded ZIPs
and extracted canonical payload were transient and removed after verification.
