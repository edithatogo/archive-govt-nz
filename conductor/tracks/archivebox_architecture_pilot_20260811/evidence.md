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

## Phase 3 - Local assurance checkpoint

`./scripts/validate.ps1` passed in full after two fail-closed corrections:

- renamed the ArchiveBox workflow-contract test to avoid a pytest module-name
  collision with the existing redundancy suite;
- rewrote a credential-rejection fixture so secret scanning remained green
  without weakening the test.

Final local results: 323 tests passed; 96.01% overall branch coverage; 100%
ArchiveBox pilot line/branch coverage; all 24 targeted repository mutations
killed (including 7/7 ArchiveBox mutations); 12 schemas validated; dependency
audit, licence policy, secret scan, and 82-component CycloneDX SBOM passed.

### Hosted pilot attempt 1

Run [31459916359](https://github.com/edithatogo/archive-govt-nz/actions/runs/31459916359)
failed closed before capture. Input validation and the immutable image pull
passed; ArchiveBox v0.7.4 exited with `No archivebox index found` because the
new mounted collection had not been initialized. Inventory and upload were
skipped, and no capture or admission is claimed. The corrective task adds
bounded `archivebox init` and always-retained diagnostic logs before retry.
