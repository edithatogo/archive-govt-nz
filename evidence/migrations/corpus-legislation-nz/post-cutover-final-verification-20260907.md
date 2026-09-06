# Prompt 21 terminal independent verification — 2026-09-07

This report is a fresh adversarial evaluation of the current target main, not a restatement of earlier labels. Target main is `cc6b95b2f98cf8df5ac4173dd6d2b40201d0b1e2`; the archived donor remains archived at `905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3`.

The governed seed recomputes to 500 unique LF records, 8,987 bytes, SHA-256 `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`. The historical declarations sum to 33,693 candidates. Live readbacks were independently hashed for Hugging Face (`d7fed0657325e790b9851f7aa75a9115eda584e95913d33385e3c5f4c23c2ff3`) and Zenodo (`9c82c2d090ac5ce7d6e9240122e2b182f5f11af06db9c5901b763dc57ed4029c`).

The four dimensions remain separate:

- Code/capability migration: **complete**.
- Operational-state migration: **incomplete** because the target-owned 500-work revalidation remains blocked.
- Corpus custody/recoverability: **complete**, with the documented external metadata handoff.
- Publication-identity migration: **blocked_external** pending the authorised Hugging Face target-origin publication/readback gate.

All red-team probes reject false completion: candidate counts are not records, workflow configuration is not an operation, green jobs require artefact/readback evidence, Actions cache is not durable custody, metadata is not publication, invalidated receipts are not active evidence, closed issues are not implementation, donor archival is not custody, content changes cannot silently reuse an ID, and software licences do not establish source rights.

Overall status: **INCOMPLETE**. The machine-readable matrix and evidence references are in [`post-cutover-final-verification-20260907.json`](post-cutover-final-verification-20260907.json). No feature, workflow, state, publication, donor, or hosted-setting mutation was performed.
