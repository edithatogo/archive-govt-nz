# Evidence

Evidence is accumulated by phase. A container exit code is never sufficient
evidence of capture; output inventories, hashes, roles, and hosted receipts are
reported separately.

## Phase 1 - Governed contracts and architecture

| Requirement | State | Evidence |
| --- | --- | --- |
| M-02 | implemented | Docker Hub `stable` resolved to immutable digest `sha256:1a5a3733...32327`; recorded in track metadata |
| M-06 | implemented-local | canonical `docs/archive-system-architecture.md`; generated Hugging Face card section; future release package input |
| M-08 | verified-remote | parent issue #48 with native subissues #49-#51 |

Focused metadata and release-package tests passed: 3 tests. No Hugging Face
write or new Zenodo deposition occurred in this phase.

## Phase 2 - Test-driven pilot implementation

| Requirement | State | Evidence |
| --- | --- | --- |
| M-01 | implemented-local | manual-only `.github/workflows/archivebox-pilot.yml`; no schedule trigger |
| M-02 | implemented-local | exact ArchiveBox image digest in config, manifest, metadata, and workflow |
| M-03 | verified-local | HTTPS/credential/port/fragment/host/duplicate/count rejection tests |
| M-04 | verified-local | canonical input and output JSON plus Markdown receipt commands |
| M-05 | verified-local | every output role is secondary with `authoritative_original=false` and `admission_state=not-admitted` |
| M-07 | verified-local | 100% line and branch coverage; property/metamorphic/contract/DST coverage; 7/7 targeted mutations killed |

Focused results: 34 pilot/assurance tests passed; Ruff and strict Pyright passed;
`actionlint .github/workflows/archivebox-pilot.yml` passed. The workflow has not
yet run on GitHub, so no capture is claimed.
