# Evidence

## Review-fix evidence — 2026-09-04

Three red identity mutations validated before the schema correction. The
corrected suite passes 15 tests and validates 48 schemas with 38 representative
documents. The canonical publication receipt is now independently checked for
`durable-state/v1/2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c/metadata.json`,
1,450 bytes, SHA-256
`ed886263fead010a540663515b24440db59371dbd9bb0abca2138942b44f8e74`.
This is validation hardening only; Prompt 13 remains pending.

## Live readback

- `evidence/migrations/corpus-legislation-nz/huggingface-publication/live-identity-observations.json` — SHA-256 `88c11df98bc91ad09ea6e31f735edca198d58b0ecf37f7a2d634cae5679677f5`.
- `evidence/migrations/corpus-legislation-nz/huggingface-publication/identity-reconciliation-report.json` — SHA-256 `9e63ceb813e8f5301de86869ae7d58fffbe6932e374c59fdcf3853bfee6edd1d`.
- `evidence/migrations/corpus-legislation-nz/huggingface-publication/identity-reconciliation-report.md` — SHA-256 `121ff994d98bdecfc5365257461cd7b4c54f245443a7e2e14be8783220e1b187`.

The observations bind canonical `1efa35e72c378068cfb112d060bd0502497f61b1`, historical `ea9e66fb89c3230fc478f7c6f05f1a82f4fa1174`, and DOI snapshot `1dea0c678b419a9c16fe7e363488f91d293391d3`. Canonical and snapshot non-card bytes returned HTTP 401 anonymously; historical readback was open. No remote write occurred.

## Governed candidate

- Typed registry: `config/legislation/huggingface-publication-registry.json`.
- Registry schema: `schemas/legislation-huggingface-registry-v1.schema.json`.
- Candidate manifest: `evidence/migrations/corpus-legislation-nz/huggingface-publication/publication-candidate-manifest.json`.
- Card and rights bytes plus the minimal gate checklist are hash-bound by the candidate manifest.

## Validation

Focused Prompt 15 suite: 40 passed. Full repository harness: 4,444 passed with 97.48% branch-aware coverage; 45 schemas and 35 representative documents validated; parity 9/9; all configured mutation suites passed; dependency audit found no known vulnerabilities; licence inventory, secret scan, and SBOM validation passed.

## Retained blockers

External publication approval is pending. Prompt 13 operational proof is incomplete and the selected 552 records remain `source_specific_review_required`. The candidate status is `candidate_only_not_published`; no hosted metadata or payload was changed.

## Superseding public publication receipt — 2026-09-03

The accountable maintainer authorised public redistribution of the selected 552-record state and an update to the existing canonical identity. Hugging Face revision `ae4da4ef0446f68fddd8f53279ecb1245f1529b9` first published the durable package; revision `04688f12dd687618e2085ae31f9b8a4a50a88b16` published the target-origin card and source-specific rights boundary.

`evidence/migrations/corpus-legislation-nz/huggingface-publication/publication-readback-20260903.json` records an anonymous exact-revision readback. It returned public, ungated access and reproduced:

- `canonical-state.zip`: 71,776,346 bytes, SHA-256 `2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c`;
- `metadata.json`: 1,450 bytes, SHA-256 `ed886263fead010a540663515b24440db59371dbd9bb0abca2138942b44f8e74`;
- `README.md`: 2,713 bytes, SHA-256 `d41be7b72c10b1e79754bed9b59deed5862d535b6ed0eead2a02df01392e8c4d`;
- `RIGHTS.md`: 771 bytes, SHA-256 `1cf3df1c833ab9f8a44b703a7668a91b25dfa1b2626972f89d11f7607a776d03`.

The related target GitHub Release indexes this publication. Its Git bundle preserves repository history and is not a duplicate host for the durable dataset bytes. Hugging Face remains the durable package byte authority.

This supersedes the earlier publication-blocked claim without deleting it. Prompt 13 operational proof remains independently incomplete and is not implied by publication success.

## Superseding validation

Focused Prompt 15 and related publication/reconciliation suite: 34 passed. The first full harness run retained one unrelated Hypothesis deadline flake after 4,559 passes; its exact test then passed unchanged. The second full harness passed 4,560 tests with 97.50% branch-aware coverage, 48 schemas and 38 representative documents, parity 9/9, every configured mutation lane, dependency/security audit, licence inventory, secret scan, and SBOM validation.

## Review-fix authority binding

Decision `archive-govt-nz-hf-publication-20260903-selected-552-v1` records the accountable maintainer's 2026-09-03 authorization in the canonical programme thread. The receipt binds candidate manifest SHA-256 `fb3caa39ffd3da9204f01ebd764237d276460dc61493eb809b7e207d17813646`, state manifest SHA-256 `877ba501a25570a29c1aada7979562d8c62c7f043865125cf402310eabc09544`, package SHA-256 `2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c`, and the exact permitted package, metadata, card, and rights files. The v2 schema restricts `approved_public_selected_552` to the canonical slug; both preserved identities must retain `source_specific_review_required`.

The review-fix full harness passed 4,579 tests at 97.52% branch-aware coverage, 48 schemas/38 representative documents, parity 9/9, all mutation lanes, dependency audit, licence inventory, secret scan, and SBOM validation. The superseding publication receipt SHA-256 is `38160c4683112d951351e20d68fe34198dcab797eb371d6cf6e6d91160ba9fed`.

## Superseding operational prerequisite — 2026-09-05

The earlier Prompt 13 incomplete statements are historical. Run [33800180992](https://github.com/edithatogo/archive-govt-nz/actions/runs/33800180992) succeeded at `95d5e0959158df3e5f816b012b66049135ff3d54`. The dated `huggingface-publication/operational-prerequisite-20260905.json` binds its exact hosted attempt artifact, raw receipts, software revision, recovered parent and zero-mismatch accounting.

The 552-record published durable package is the parent of the 904-record cumulative continuation. The batch reconciliation selects 852 records for 500 reviewed works; 52 retained parent works explain the difference. Neither the continuation nor its additional versions are claimed as published to Hugging Face.

`huggingface-publication/live-identity-audit-20260905.json` records independent anonymous API and fixed-revision reads for all three existing identities. Canonical card and durable-package metadata describe the selected 552-record state. Its preserved legacy manifest describes 95 donor-era records, and the historical legacy manifest describes 6,609 records. These are distinct surfaces. Viewer `default/validation` contains one validation-report row, not a corpus count. The immutable DOI identity is gated: listed files are not evidence of anonymous payload access. Historical body wording is preserved as historical documentation; its top-level superseded role remains explicit.

Monthly reconciliation explicitly selects the canonical slug and compares the selected-state card roots/counts and rights to the governed publication registry; it does not equate legacy manifest or viewer row counts to selected-state counts. No identity, DOI, immutable snapshot or remote payload changed during this closeout.

### Acceptance reconciliation

| Requirement | Evidence and boundary |
| --- | --- |
| Three non-conflicting identities | Dated live audit fixes each exact revision and role; historical and DOI identities unchanged. |
| Target authority and donor lineage | Canonical fixed-revision card metadata names target authority and exact source commit; its body retains operational donor SHA. |
| Evidence-based rights and coverage | Public selected-state approval remains limited to 552; candidate 33,693 and reviewed 500 counts are not complete coverage. |
| Monthly canonical reconciliation | `.github/workflows/monthly-legislation-reconciliation.yml` passes the canonical slug to both tools; registry and card selected-state roots/counts agree. |
| Exact remote-write readback | September 3 publication receipt remains immutable; September 5 anonymous streaming download independently reproduces the exact approved package hash. |
| Prompt 13 prerequisite | Successful exact run, signed-in GitHub artifact download with remote digest comparison, raw continuation/harvest/lineage/reconciliation receipts, and registry hash binding. |

Dated live audit SHA-256: `ab4bf796bde6c323389a87869fac71a539f2638cffd25b1c1965adf69d9c6f38`. Operational prerequisite receipt SHA-256: `bcfa99bedd7b08bf6a4c079c08fe61c2a3d752210095c0476fb7b54df5cd9411`. These are verification additions; no external write was necessary.
