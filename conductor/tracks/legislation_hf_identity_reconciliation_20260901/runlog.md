# Run log

## Operational prerequisite closeout — 2026-09-06

Read all three public identity APIs anonymously and streamed all four approved
canonical files from the exact pinned revision, checking size and SHA-256.
`evidence/migrations/corpus-legislation-nz/huggingface-publication/operational-reconciliation-20260906.json`
records successful readback without publication. The registry now binds the
independently verified Prompt 13 receipt from `hosted-closeout-20260906`.

Red: `uv run --locked pytest tests/tools/test_legislation_huggingface_registry.py -q --no-cov`
failed on the old blocked-receipt digest (1 failed, 14 passed).
Green after registry/schema correction and negative evidence-path fixtures:
the same command passed all 17 tests. Ruff lint and format checks passed.

The baseline full `./scripts/validate.sh` passed all stages (4,799 tests).
The final-tree run reached 4,800 passes and one timing-only Hypothesis failure:
`tests/publication/test_zenodo_identity.py::test_noncanonical_concept_dois_are_rejected`
took 262.81 ms once and 31.35 ms on replay against its unchanged 200 ms deadline.
No assertion failure was reported. Recovery uses an unchanged focused replay
and the existing `PYTEST_XDIST_AUTO_NUM_WORKERS=2` setting to reduce contention;
test deadlines, examples, coverage thresholds and harness stages are unchanged.

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

Additional outcomes are preserved in `validation-additional-attempts-20260905.json`: the second focused rerun had one further algebra timing flake; the one-worker run was deliberately interrupted after 730 passes and two deadline flakes; the separately executed post-test gates stopped at a checkpoint mutation subprocess timeout. None is a local full-pass claim. Independent hosted Ubuntu and macOS full harnesses each passed all 4,742 tests at 97.60% coverage on `abfd287a18be654b7bbc97e5c536ac144d4ef268`, plus all configured downstream gates. Windows remains pending at this entry.

## PR review follow-up

Full final-head checks passed at `2eb2a1449b6b562455391dfe9a9e873c936e6540`, but two subsequent review findings prevent merge. The duplicate-slug schema finding reproduced with six red tests, then all 27 focused/property tests passed after exact-once constraints. The constraint-removal mutation was detected by all six negative cases. A lint finding on a positional Boolean test parameter was corrected with a keyword-only argument. Historical v1/v2 remain unchanged.

The Prompt 13 formal-prerequisite review exposed a missing credential/endpoint no-write check, not merely a status typo. The owning issue #335 was reopened for its separately reviewed fix and named superseding reports. Prompt 15 metadata/plan are explicitly in progress until that full prerequisite passes. The registry's operational-proof Boolean remains factual about the independently verified run; it is not a claim that every Prompt 13 action is complete.

## Ordered operational binding preparation — 2026-09-05

The registry now identifies the immutable specialist-owned ordered proof for run 33968609350 and preflight 33968519628 by governed path and SHA-256. Delivery of that P13 receipt remains pending; the P15 prerequisite gate is not yet satisfied. The new monthly readback/comparison confirms the same approved 552 canonical publication with zero mismatches. No remote metadata or payload write was necessary. P13 residual second 904-parent cycle is not converted into a pass, and no 904 publication is claimed. The original 33800180992 proof and earlier readbacks remain preserved.

## Merged ordered operational input — 2026-09-06

PR #406 merged at `abce27ae6b3043e10d96a48e3b386b1c4f70d7b0`. The specialist-owned `ordered-20260905/ordered-operational-proof.json` exactly matches SHA-256 `fb1a345a3ec2d20c4e3f744a426abbf0928a1e7050a1fdee6a0b007099804671`. It proves the ordered 500-work run 33968609350 after source preflight, with zero unexplained mismatches. This supersedes earlier statements that Prompt 15 must wait for all of issue #335 to close: its actual prerequisite is verified operational proof, now delivered. The separate second 904-parent continuation remains an explicit Prompt 13 blocker; no 904-record publication is claimed. Prompt 15 remains in progress until its own final validation and hosted checks pass.

## Prompt 15 acceptance closeout — 2026-09-06

The three live revisions remain unchanged. Anonymous canonical README, RIGHTS, and package metadata hashes and sizes exactly match the authorized 552-record publication receipt. The refreshed monthly comparison has zero mismatches. All Prompt 15 acceptance evidence is satisfied; delivery through PR #396 remains conditional on required exact-head hosted checks and protected merge. This supersedes the earlier in-progress statement for this issue only. No new remote dataset write was needed. The independent Prompt 13 second904-parent continuation is not marked complete. See `live-readback-refresh-20260906.json`, `monthly-comparison-20260906.json`, and `final-validation-20260906.json` in the Hugging Face publication evidence directory.
