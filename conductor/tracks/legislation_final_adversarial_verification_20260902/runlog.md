# Run log

- 2026-09-02: Fetched target main `f42cbbfe...`; independently confirmed donor archived at `b40587f...`.
- 2026-09-02: Three independent audits reviewed repository claims, state/custody artefacts, and live hosted/publication state.
- 2026-09-02: Recomputed the governed seed, historical batch arithmetic, referenced receipt hashes, and current API response hashes.
- 2026-09-02: A broad-search Zenodo drift finding opened #357; direct field inspection disproved it. Posted the correction and closed the issue without code changes.
- 2026-09-02: Classified all four dimensions incomplete and preserved external blockers without implicit passes.
- 2026-09-02: Full `./scripts/validate.sh` passed: 4,543 tests, 97.50% coverage, 48 schemas/38 documents, 9/9 parity, all registered mutations, dependency/licence/secret/SBOM gates, and 363.89 MB/s bounded CAS.
- 2026-09-02: Exact live target-main CI, CodeQL workflow, and workflow-policy runs all completed successfully. Two existing high-severity CodeQL alerts remain open and main remains unenforced.
# Current-state refresh — 2026-09-03

- Re-read Issue #357: closed as a false-positive Prompt 16 finding.
- Re-read live code-scanning: both high-severity URL alerts are `fixed`.
- Re-ran workflow lint: zero findings.
- Confirmed active `main-integrated-assurance` ruleset with required exact-head
  checks.
- Operational recovery, custody, publication, and release gates remain
  unresolved; no completion claim or external mutation was made.
# Superseding independent acceptance — 2026-09-06

Current result: **INCOMPLETE**. The dated independent matrix and report at
`evidence/migrations/corpus-legislation-nz/independent-final-acceptance-20260906/` supersede historical status claims below.
First-cycle operation, approved 552-record durable custody and publication are
verified. Actual hosted parent metadata rejects the exact-inventory output name
(`HOSTED-PARENT-NAME-001`, issue335; Prompt08 owner, Prompt06 consumer).
Parent delegated compatibility repair to Lovelace and retains P13/P15 active.
Second-cycle execution is a Should in the original track, while the interface
defect is a concrete integration limitation. This audit changes only Prompt01/21
track-local records and dated new evidence. No publication, push, merge or archive.

See the dated `validation.json` for local harness attempts and `report.md` for
primary readbacks, exact source hashes, scope limits and remaining delivery gates.
