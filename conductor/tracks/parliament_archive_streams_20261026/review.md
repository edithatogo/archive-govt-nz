# Review Report: Parliament archival streams

## Summary

The bounded public-report lane has manual remote proof; broader submission/advice, scheduling and full-archive acceptance remain incomplete.

## Verification Checks

- [ ] **Plan Compliance**: Partial — report discovery/capture/publication implemented; P1/P3 mixed-source qualification, P4 natural schedule/reconciliation and P5 expansion remain open.
- [x] **Style Compliance**: Pass — Ruff format/lint; whole-project type gate passed after correcting optional schema-version lookup.
- [x] **New Tests**: Yes — 74 synthetic contracts for source drift, integrity, public visibility, immutable provenance, bounded capture and independent recovery.
- [ ] **Test Coverage**: Partial — focused contracts pass; full suite aggregate coverage 97%; mutation/supply-chain stages pending. No assertion of 100% policy-critical coverage or Parliament-specific mutation completeness.
- [ ] **Test Results**: Passed tests — 8,423 passed, 14 capability skips; full remaining harness running. Focused suite 74 passed, strengthened provenance regression passed separately. Native report and metadata-only batches anonymously verified.

## Findings

### High — source access/reuse gates prevent broader acceptance

- **File**: `conductor/tracks/parliament_archive_streams_20261026/evidence.md`
- **Context**: Legacy robots denies crawling; submissions and most committee advice are outside the general reuse grant. The report pilot cannot satisfy the complete mixed business-item acceptance criterion.
- **Resolution**: Keep those lanes gated and parent/phase issues open; no rights bypass, private fallback or completion claim.

### Medium — natural schedule and historical reconciliation remain unproven

- **File**: `src/archive_govt_nz/parliament/worker.py`
- **Context**: Recent first-page windows and resumable offset history can miss late or shifted entries. A manual run does not prove recurrence; acquisition deadlines exclude publication time. Discovery/state overhead is not a qualified whole-root hard spool cap.
- **Resolution**: Retain explicit operational limits; do not claim complete coverage or unattended acceptance. Qualify ongoing scheduling, periodic full reconciliation and total-spool guard before scale-up.

### High — old bytes must retain their original metadata (fixed)

- **File**: `src/archive_govt_nz/parliament/pipeline.py`
- **Context**: Joining captures directly to the current record could relabel an old file with newer title metadata.
- **Resolution**: Immutable observation snapshots now bind source ID, URL, byte hash and record hash. A regression changes metadata and payloads, then asserts old/new titles against their exact hashes. Passed.

### Medium — unknown upload outcomes must not repeat mutations (fixed)

- **File**: `src/archive_govt_nz/parliament/publication.py`
- **Context**: A lost commit response could otherwise cause an unnecessary second write or overwrite.
- **Resolution**: Check the immutable remote namespace, download and compare every existing file, reject partial/conflicting state; use observed parent revision and one mutation at most. Synthetic recovery contracts passed.

Reviewed all new Parliament source modules, CLI entry point, schemas and synthetic tests iteratively, plus changes to the validation-schema registration. No secrets or source personal payloads added to Git; fixtures are fictional. Public report originals remain on Hugging Face with hash-bound eligibility assertions. The unfinished parent track must remain active, not archived.
