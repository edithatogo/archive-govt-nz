# Review Report: Parliament archival streams

## Summary

The bounded public-report lane has manual remote proof; broader submission/advice, scheduling and full-archive acceptance remain incomplete.

## Verification Checks

- [ ] **Plan Compliance**: Partial — report discovery/capture/publication implemented; P1/P3 mixed-source qualification, P4 natural schedule/reconciliation and P5 expansion remain open.
- [x] **Style Compliance**: Pass — Ruff format/lint; whole-project type gate passed after correcting optional schema-version lookup.
- [x] **New Tests**: Yes — 74 synthetic contracts for source drift, integrity, public visibility, immutable provenance, bounded capture and independent recovery.
- [ ] **Test Coverage**: Partial — focused contracts pass; full suite aggregate coverage 97%; repository mutation stages passed; all supply-chain stages passed after exact synthetic-fixture correction. Four added Parliament policy mutants killed; no assertion of 100% policy-critical coverage.
- [x] **Test Results**: Passed tests — 8,423 passed, 14 capability skips; all remaining stages passed; secret scan resumed after exact synthetic-fixture correction. Focused suite 74 passed, strengthened provenance regression passed separately. Native report and metadata-only batches anonymously verified.

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

## Follow-up metadata hardening review

44 native cards and four collection readbacks audited. Corrected stale zero counts, missing source ZIP description, licence/identity overclaims and unsafe table auto-detection. Maintained public card replacements are revision-conflict protected; original payloads and gates preserved. Publication regression tests cover maintained-card preservation, unknown counts and missing explicit-card failure before native writes. The full-suite snapshot mismatch was the expected reviewed metadata change; updated snapshot and eleven affected tests pass. Other assurance stages passed. Remaining hosted conversion acceptance and source acquisition blockers remain explicit; no incomplete track archived. See docs/huggingface-estate-hardening.md and versioned receipts.

Final P6 acceptance: all14 configured tabular datasets and41 first-row probes pass. Historical reader101/RNZ74 rows pass on isolated Python3.15.1. Registry/collection native readbacks and exact revisions retained. Public collection-ID scan findings are adjudicated only for the byte-identical reviewed receipt; 27 supply-chain tests, including changed/unrelated-file rejection, pass. Types pass. Native metadata setup is complete for the44-dataset scope; parent archival gates remain independent and active.

## Windows hosted-check follow-up

Repeated cancellation was diagnosed through native annotation as an aggregate30-minute job timeout, not a reported failing test. A single targeted rerun had the same outcome; no further blind rerun. Reviewed conditional Windows60-minute allowance, unchanged required commands and1200-second per-command gates,55-minute step ceiling, pipefail exit propagation and always-upload diagnostics. Actionlint and21 focused workflow/harness tests passed. Hosted outcome remains pending; no archive scaling or merge accepted.
