# Run Log

## 2026-08-11

- Initialized bounded ArchiveBox evaluation after explicit approval.
- Resolved Docker Hub `stable` to immutable manifest digest
  `sha256:1a5a37331091d9df865ead2b9c231aa5a892fc26fe0422ce6140d9e2d9532327`.
- Confirmed local Docker and WSL are unavailable; canonical execution remains a
  Linux GitHub Actions job rather than a local installation.
- Created GitHub parent issue #48 and native phase subissues #49-#51.
- Added the canonical reusable Mermaid architecture profile and wired it into
  generated Hugging Face card material and future Zenodo release packages.
- Passed 3 focused publication-metadata and release-package tests.
- Observed the required red phase: pilot tests initially failed because the
  module and workflow did not exist.
- Implemented fail-closed pilot manifests and inventories, paired receipt tools,
  three reviewed official HTTPS candidates, and the manual hosted workflow.
- Achieved 100% line/branch coverage for `archivebox_pilot.py`, passed 34 focused
  tests, and killed all 7 targeted integrity/policy mutations.
- Corrected a pytest basename collision and a secret-scan false positive without
  weakening either contract.
- Completed the full Windows validation harness: 323 tests, 96.01% overall
  branch coverage, all 24 targeted mutations killed, and all supply-chain gates
  passed.
- Hosted run 31459916359 failed before capture because the fresh mounted
  collection required `archivebox init`; no capture or admission was claimed.
- Added bounded initialization and always-retained init/add diagnostic logs as
  the retry correction.
- Hosted retry run 31460195023 completed, but review found that its receipt
  inventoried files without reconciling extractor outcomes per candidate.
- Added bounded per-snapshot parsing, exact candidate reconciliation, redacted
  extractor states, and explicit original-payload denial in commit `3fdf3c0`.
- Hosted run 31460943846 succeeded on revision `3fdf3c0`: 3 snapshots, 43
  hashed files, 2,598,932 bytes, and receipt SHA-256
  `69dece6db2e91b3d2f07cf009d0e9ea5374685fe4e36a1ad545c4488f515c1e1`.
- Each candidate reported 9 successful and 3 failed extractors. All three wget
  captures failed with HTTP 403; two browser renders captured access-challenge
  pages. No original payload was verified and nothing was admitted.
- The complete harness passed: 330 tests, 96.13% branch coverage, 100% pilot
  coverage, 9/9 pilot mutations, and all supply-chain gates.
- The authorized Hugging Face documentation update was attempted. The current
  credential identified `edithatogo`, but direct commit and protected PR
  pre-upload both returned HTTP 403. No remote file changed.
- Final hosted CI caught a secret-scan false positive on a revision-valued
  metadata key. Renamed the key to the scanner's governed `revision` field;
  the digest value and security policy were unchanged.
