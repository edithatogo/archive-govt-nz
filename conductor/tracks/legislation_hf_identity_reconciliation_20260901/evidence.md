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
