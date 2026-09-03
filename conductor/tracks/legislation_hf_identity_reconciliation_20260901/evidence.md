# Evidence

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
