# Run log

- 2026-09-01: fetched target main and independently read donor archive/head.
- 2026-09-01: three parallel read-only audits inspected prerequisites, workflow/credential contracts, and independent verification design.
- 2026-09-01: observed Prompt 06 issue #308 open; Prompt 10 issue #327 and preparation-only draft PR #329 open.
- 2026-09-01: observed the governed 500-line seed and registry hash; no source acquisition occurred.
- 2026-09-01: no dispatch attempted because the current lane is discovery-only, its cap is 50, the compatible parent reference is absent, and Prompt 08 sealing is incompatible with Prompt 12 v3 receipts.
- 2026-09-04: superseding live readback confirmed Prompt 06 and Prompt 10 are merged, the exact-inventory lane is present, and `config/legislation/parents/current.json` is committed on `main`.
- 2026-09-04: authorized run `33772828586` passed seed and parent restoration, then was manually cancelled during the 500-work acquisition step after about six minutes. The workflow's configured timeout is 360 minutes; elapsed time did not prove a stall. No acquisition, reconciliation, sealing, or recovery claim is made.
- 2026-09-04: run `33772828586` reached terminal `cancelled` state. Retained artifacts verify parent lineage/restoration and the sanitized attempt seed; reconciliation is `failed` with `mismatch_count=1`, while acquisition, verify/accounting, and continuation were skipped. Operational proof remains blocked pending a complete authorized execution.
- 2026-09-04: PR #373 assurance runs `33773918650`, `33774276982`, and `33774503187`, plus CodeQL run `33774503447`, were manually cancelled after roughly one to three minutes. Historical successful CI runs take about 10–13 minutes, and GitHub's run-level `updatedAt` does not update continuously during a running step; these cancellations do not establish a runner or workflow hang. Workflow policy lint `33774503378` passed.
- 2026-09-04: the exact locked assurance command subsequently completed locally without modification: 4,592 tests passed with 97.52% coverage, 48 schemas/38 representative documents, parity 9/9, every configured mutation lane, dependency and licence audits, secret scan, and 111-component SBOM validation. This corrects the earlier hang diagnosis but remains local evidence, not a hosted check or Prompt 13 operational proof.
- 2026-09-01: first repository harness attempt stopped at Conductor validation because the new in-progress track used a blocked metadata status and a noncanonical gate status. Both were corrected without weakening the validator.
- 2026-09-01: repeated harness passed 4,393 tests at 97.48% coverage, schemas and parity, then the secret scan correctly flagged a receipt-keyword candidate. The key was renamed; the repeated secret scan and SBOM validation passed.
- 2026-09-03: re-read target `e559d675c347615d64ae5e1c1f3ad5efd5d120f6`
  and archived donor `b40587f1b1aec7356a0f623916fcc8212397d283`.
- 2026-09-03: verified Prompt 06 merged through PR #362 and the v3
  parent-state compatibility through PR #364. The active exact-inventory
  workflow has no runs.
- 2026-09-03: confirmed the committed parent reference remains absent. No
  credential access, live preflight, parent restore, workflow dispatch, or
  state write occurred.
- 2026-09-03: focused exact-workflow and parent-state tests passed 107 tests;
  actionlint returned no findings; governed seed bytes revalidated at 500
  unique sorted LF lines and the registered SHA-256.
- 2026-09-03: `./scripts/validate.sh` passed 4,559 tests at 97.50% coverage,
  48 schemas/38 documents, 9/9 parity, all registered mutation lanes,
  dependency, licence, credential-scan, and 111-component SBOM gates.
# 2026-09-03 — identity contract correction

- Addressed PR #365 panel P1: unified parent restore and seal execution identity
  on `${{ github.run_id }}`; retained `batch_id` as batch correlation only.
- Added static workflow-integrity regression coverage.
- No hosted execution dispatched; operational gates remain fail-closed.
- Reviewed and validated the durable parent-reference implementation: 111
  focused tests passed and schema validation covered 48 schemas/38 documents.
  No live Hugging Face retrieval or parent adoption occurred.


# 2026-09-03 — durable parent selected and preflighted

- Observed Prompt 15 merged at `d60ed58420d1fe39dc420bbe047b9bf901b0d66d` and Prompt 10 merged at `5745bf3e38924dc968af70842dc6ed7a776e9e05`.
- Pinned the approved public Hugging Face package at revision `ae4da4ef0446f68fddd8f53279ecb1245f1529b9`, exact size 71,776,346 and SHA-256 `2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c`.
- Retained failed preflight attempts for noncanonical reference bytes and an incorrect conflation of historical package rights with later publication authority. The correction validates both facts independently.
- The third repository-native no-write preflight restored 555 files and reproduced manifest root `877ba501a25570a29c1aada7979562d8c62c7f043865125cf402310eabc09544` and inventory root `9ca6dc505f991e015c6c997827878d8c7e9381b214a1544eb338328a285c6894`.
- No credential was read and no source acquisition, hosted dispatch, state upload, or publication occurred. The authorized hosted run remains pending merge and green exact-head checks.
- Hosted CI run `33747996055` preserved the first exact-head failure: Ubuntu job `100625110025` and macOS job `100625110041` rejected `authority_git` because the default shallow checkout omitted the pinned Prompt 15/10 commits; Windows job `100625109830` was cancelled by the superseding push. The fix retains full checkout history in CI and the operational workflow; no lineage check was weakened.
