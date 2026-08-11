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
