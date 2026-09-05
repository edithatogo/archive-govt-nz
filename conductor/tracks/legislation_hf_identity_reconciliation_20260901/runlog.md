# Run log

- 2026-09-01: fetched target main `ff01566b5e6fff2f4e2b5f93ecdec11bb0c3c7e8`; confirmed donor archived at `b40587f1b1aec7356a0f623916fcc8212397d283`.
- 2026-09-01: created issue #341, branch `codex/legislation-hf-reconciliation`, and an isolated clean worktree.
- 2026-09-01: publication gate retained as pending; repository-owned audit and candidate work continues independently.
- 2026-09-01: implemented exact-revision identity parsing, separate rights inventory/access semantics, a typed three-identity registry, deterministic canonical-card candidate, and fail-closed monthly comparison against `edithatogo/corpus-legislation-nz`.
- 2026-09-01: focused qualification passed 40 tests plus Conductor validation, Ruff and whitespace checks; remote publication and independent returned-revision readback remain explicitly gated.
- 2026-09-01: audited all three existing identities anonymously at immutable revisions; no remote write occurred.
- 2026-09-01: recorded canonical and DOI identities as public-metadata/auto-gated, historical as open, and preserved listed-but-access-controlled `RIGHTS.md` semantics.
- 2026-09-01: added the typed three-identity registry, immutable canonical card candidate, exact-revision verifier correction, and canonical monthly comparison.
- 2026-09-02: focused validation passed (40 tests); full `./scripts/validate.sh` passed with 4,444 tests, 97.48% coverage, all mutation lanes, schema/parity, supply-chain, licence, secret, and SBOM gates green.
- 2026-09-02: retained external publication gate as pending. Prompt 13 operational proof and item-level rights review remain blockers; candidate was not uploaded.
- 2026-09-03: refreshed target `main` at `e559d675c347615d64ae5e1c1f3ad5efd5d120f6`; confirmed the donor remains archived. The donor presentation head is `905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3`; the final operational lineage remains `b40587f1b1aec7356a0f623916fcc8212397d283`.
- 2026-09-03: recorded the accountable authorization for public redistribution of the selected 552-record state and the two existing-identity Hugging Face commits: durable package `ae4da4ef0446f68fddd8f53279ecb1245f1529b9` and card/rights `04688f12dd687618e2085ae31f9b8a4a50a88b16`.
- 2026-09-03: the first anonymous readback command used unavailable `python` and exited 127 without network access; the bounded correction used `python3`.
- 2026-09-03: anonymous exact-revision readback returned `private=false`, `gated=false`, 114 files, and reproduced the exact README, RIGHTS, metadata, and 71,776,346-byte package hashes. No credential was supplied to the verifier and no local copy was retained.
- 2026-09-03: focused Prompt 15 validation passed 34 tests, Ruff, v2 registry schema validation, and Conductor state validation. The first full harness attempt reached 4,559 passing tests and 97.50% coverage but failed one unrelated Hypothesis 200 ms deadline check; the same test passed alone without modification.
- 2026-09-03: the second full `./scripts/validate.sh` passed: 4,560 tests, 97.50% coverage, 48 schemas/38 documents, parity 9/9, every configured mutation lane, dependency audit, licence inventory, secret scan, and SBOM validation.
- 2026-09-03: PR review found that the publication decision was not explicitly bound to the candidate hash/permitted files and that the shared identity schema allowed rights-status broadening. Added stable decision `archive-govt-nz-hf-publication-20260903-selected-552-v1`, approval source, candidate/state/package hashes, the exact four-file allowlist, and canonical-slug conditional rights validation.
- 2026-09-03: review-fix full `./scripts/validate.sh` passed on current base: 4,579 tests, 97.52% branch-aware coverage, 48 schemas/38 documents, parity 9/9, all mutation lanes, dependency audit, licence inventory, secret scan, and SBOM validation.
- 2026-09-03: implementation continuation confirmed publication/readback evidence is complete, but the final task remains pending because Prompt 13 operational proof is a named prerequisite. No additional Hugging Face mutation was attempted.
- 2026-09-04: review regressions proved the v2 schema allowed role/provenance
  swaps between the three fixed slugs. Slug-specific schema conditionals now
  bind role, origin metadata, mutability, and gating. The readback test also
  independently pins the authorized `metadata.json` path, 1,450-byte size, and
  SHA-256. All 15 registry tests and all 48 schemas/38 documents pass.

## 2026-09-05 — Operational prerequisite reconciliation

Fresh target main: `f2669f1ce6ae48f3e09387608acbb8c58aa20334`. Donor remains archived at redirect head `905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3`; final operational donor remains `b40587f1b1aec7356a0f623916fcc8212397d283`. No audited baseline SHA was supplied by Prompt 15.

Downloaded run 33800180992 sanitized attempt artifact 9911101072 again; exact ZIP SHA-256 matched the hosted digest. Preserved five original JSON receipt byte streams and bound their hashes to the dated operational prerequisite receipt. Independent anonymous Hugging Face audit confirms unchanged revisions and durable package fixity. No remote dataset write was performed.

Red test run: 11 failed and 4 passed because the new v3 schema and successful prerequisite receipt did not yet exist. Added a superseding schema, preserving v1/v2. The registry now records operational proof while retaining the published 552-record state. Pending full validation and hosted checks; no terminal closeout claimed.

First full harness: 4,706 passed, six timing/health-check failures, 97.58% coverage. Failed attempt is preserved in `validation-attempt-01-20260905.json`; unchanged serial rerun and two-worker harness follow. No thresholds or test selection weakened.

All six first-attempt failures passed unchanged in a serial rerun. Rebased onto main `3c867a9e3140a9575ebe5a2805c98ea85119cb5b` (unrelated health readiness merge). Second full run with two workers: 4,740 passed, two Hypothesis deadline flakes, 97.60% coverage; both initial examples passed on replay. `validation-attempt-02-20260905.json` preserves the outcome. A one-worker third run is underway. Draft PR hosted CI will provide independent runner evidence; no local success or merge readiness is claimed from the failed runs.

The monthly public readback and canonical selected-state comparison executed successfully and are preserved separately. This resolves the prior recovery metadata handoff without broadening the published payload.
