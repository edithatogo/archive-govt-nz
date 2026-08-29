# Run Log

## 2026-08-29 — Track initialization

- Confirmed the repository root at
  `/Volumes/PortableSSD/GitHub/archive-govt-nz` and preserved a clean worktree
  on local `main`, which was 17 commits ahead of `origin/main` before this
  scaffold.
- Read the project definition, requirements, design, technology stack,
  workflow, autonomy policy, tracks registry and applicable repository rules.
- Ran `./scripts/validate.sh` before scaffolding. The full local baseline
  passed: lock, formatting, lint, strict typing, 1,161 tests with 95.36%
  coverage, schemas, parity, mutation lanes, hygiene, CAS benchmark,
  dependency audit, licence checks, secret scan and SBOM validation.
- The validation harness updated four timestamp-bearing evidence receipts.
  Their diffs were inspected and restored as known generated churn; no
  substantive evidence change was retained.
- Cloned the public donor read-only and pinned commit
  `4668e6c3b1b492086941d4c1ef96e299250a8301`, tree
  `c6d44ff79eda73cfc6ba7db5764e27ce01b890e1`, and deterministic Git archive
  SHA-256
  `9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e`.
- Verified the donor inventory contains 23 tracked files (6,604,301 bytes):
  eight original source files, one five-table/312-row SQLite database, three
  Python scripts, six PNG plots, and five documentation/licence files.
- `python -m py_compile process_data.py` identified an `IndentationError` in
  the donor. This is characterization evidence and a regression target; donor
  code was not executed as trusted production code.
- Inspected the current Hugging Face HEOR collection read-only. It exists and
  was public; only `edithatogo/reimbursement-atlas` was observed as a member.
  No health-appropriations dataset was created or uploaded.
- The spreadsheet capability lookup reported that bundled workspace workbook
  dependencies were not configured. No alternate parser was silently used;
  executable workbook inventory and dependency evaluation are explicit Phase
  1 tasks.
- Reviewed official discovery leads for Treasury/Budget Vote Health and fiscal
  series, Ministry of Health Vote Health series, Pharmac CPB, and Stats NZ
  context. These remain planning observations pending a live cutoff-bound
  source census and resource-level rights evidence.
- User explicitly approved the revised medallion-aligned specification and
  plan, including complete original retention and the direct/indirect dataset
  recommendations.

## Initialization boundary

No source payload was copied into this repository, no archive CAS was mutated,
no new dependency was adopted, no external issue was created, and no GitHub or
Hugging Face publication state was changed during planning.

## 2026-08-29 — Post-scaffold validation

- Track structural checks passed: all 19 Must requirements and all 16
  acceptance criteria appear in the plan; all ten required artifacts exist;
  metadata and four JSONL evidence records parse; the registry link resolves;
  and `conductor/index.md` is unchanged.
- `./scripts/validate.sh` passed after the scaffold: lock, Ruff format/lint,
  basedpyright, 1,161 randomized tests in 190.84 seconds, 95.36% coverage, 30
  schemas and 20 representative documents, 9/9 parity checks, every targeted
  mutation lane, zero hygiene findings, 590.54 MB/s CAS benchmark, no known
  dependency vulnerabilities, licence inventory, source-scoped secret scan,
  and a validated 102-component CycloneDX SBOM.
- Four harness-generated timestamp-only evidence diffs were inspected and
  restored. They were unrelated to this planning track and are not included in
its change set.

## 2026-08-29 — Phase 0.1 implementation baseline

- Re-observed local commit `160d1705ee93d898c635f094fe98d8ae14d16695`
  and remote `main` at `b5f736010a47f5a260dca35d5ee3f4dbcadb4de7`.
- Re-cloned the donor read-only at its pinned commit. Its remote ref, tree,
  no-prefix deterministic Git archive digest, 23 paths, 6,604,301 bytes,
  eight originals, five SQLite tables/312 rows, three scripts and six plots
  all match the planning baseline. A prefixed archive has a different digest,
  as expected; the receipt therefore names the no-prefix archive contract.
- Observed all eight official landing-page leads. Pharmac and both Stats NZ
  pages returned HTTP 200; the four Treasury/Budget pages and Ministry page
  returned bounded HTTP 403 responses to the command-line client. These are
  availability observations, not source-item dispositions or capture claims.
- Confirmed Hugging Face authentication as `edithatogo`, absence of the target
  dataset, and one existing HEOR collection member. No matching GitHub issue
  exists. No hosted state was changed during this reconciliation.
- Recorded the local toolchain versions for `uv`, Python, GitHub CLI,
  Hugging Face CLI and Git. DuckDB and LibreOffice executables were not found
  on `PATH`; repository-managed Python capabilities are evaluated separately.

## 2026-08-29 — Phase 0.2 hosted issue hierarchy

- Created parent GitHub issue
  [#205](https://github.com/edithatogo/archive-govt-nz/issues/205) and phase
  issues #206 through #216 under the user's explicit instruction to complete
  the remaining track work.
- Added all eleven phase issues as GitHub sub-issues of #205 and independently
  read the hierarchy back through the API. Issue creation is now evidenced;
  issue closure remains tied to the corresponding phase evidence.

## 2026-08-29 — Phase 0 checkpoint

- Reviewed the reconciled baseline for drift, unsupported completion claims,
  credentials, signed URLs and restricted payloads; no actionable finding was
  identified.
- `./scripts/validate.sh` passed: lock, format, lint, strict typing, 1,182
  tests in 121.17 seconds, 95.33% coverage, 30 schemas, 20 representative
  documents, 9/9 parity checks, all mutation lanes, hygiene, 423.38 MB/s CAS,
  dependency audit, licence inventory, secret scan and a 102-component SBOM.
- Four known timestamp-bearing validation receipts were inspected and restored
  rather than retained as unrelated generated churn. This is local Phase 0
  readiness evidence, not hosted CI or publication evidence.

## 2026-08-29 — Donor Bronze import and first source census

- Added typed, fail-closed source inventory and donor-manifest contracts plus
  safe XLSX/PDF/SQLite structural inventory.
- Imported all 23 donor paths (6,604,301 bytes) into 23 immutable SHA-256/BLAKE3
  objects outside Git and verified every object from the generated manifest.
  The manifest and format-census SHA-256 digests are recorded in machine
  evidence; payload paths are intentionally not committed.
- The seven workbooks contain 152 sheets, 2,388 formula cells, two hidden
  sheets, 5,777 named ranges, six charts and 11 external links. The PDF has
  471 pages; the five-table SQLite derivative has 312 rows. Inventory did not
  mutate an original.
- Built a 2026-08-29 census with 79 official records: 66 links exposed by the
  complete Vote Health index and 13 current direct/context resources. All are
  `discovered`; none is mislabeled captured or rights-cleared. Earlier annual
  Budget/forecast vintages and exact Stats NZ QES/population series remain to
  enumerate before Phase 1 completeness.
- Adopted locked `openpyxl` and Matplotlib adapters without adding Pandas.
  Focused tests and strict typing passed. Dependency audit and licence
  inventory passed; a scanner keyword false positive in existing machine
  evidence was renamed without suppression, after which the tracked-source
  scan and 110-component SBOM passed.
- The first staged-source scan failed closed on one unverified keyword finding:
  a machine-evidence key named `secret_scan`. Inspection of the bounded receipt
  confirmed that no token or credential was present. The field was renamed to
  `tracked_source_scan`; no detector suppression was added, and the staged
  source scan then passed with zero candidates.

## 2026-08-29 — Bronze through Platinum implementation checkpoint

- Expanded all 66 historical Vote Health edition pages to 58 unique official
  PDFs, including the two directly resolved 2012/13 supplementary-estimates
  files. Added current Budget/BEFU/HYEFU/Fiscal Time Series, Ministry Vote
  Health, Pharmac CPB, and exact Stats NZ CPI, QES, population-benchmark and
  current-price GDP inputs.
- Closed the cutoff-bound census at 141 records: 73 captured originals and 68
  discovery-only pages represented by their authoritative resources. No item
  remains discovered or retryable. The complete capture contains 73 matching
  WARC receipts and 38,584,141 source bytes in immutable external CAS.
- Produced 312 typed Silver facts and 1,699 field-lineage records from the
  verified donor parity oracle. Rebuilt its five-table SQLite database with
  exact row/value parity, five analytical Parquet products and all six plots.
- A clean-room rebuild from Bronze reproduced both Silver Parquet digests and
  all 12 Gold artifact digests byte-for-byte when supplied the pinned
  observation time. A deliberately different observation time changed the
  bitemporal facts digest, demonstrating that time is part of the identity.
- Built candidate v4 with 94 pre-manifest files and 39,390,246 bytes. Its
  manifest SHA-256 is
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`;
  rights and source-disposition gates pass, while upload remains gated on
  explicit approval of this exact manifest.
- Final local `./scripts/validate.sh` passed at commit
  `f32f0fbdb223fa0358c91defcc749ce9cb739d2f`: 1,200 tests, 95.16% coverage,
  30 schemas, 20 representative documents, 9/9 parity checks, all mutation
  lanes, hygiene, CAS benchmark, dependency audit, licences, secret scan and
  110-component SBOM. Seven resource warnings were reported but did not fail
  the harness; they are not hidden.

## 2026-08-29 — GitHub merge and Hugging Face publication

- PR #217 passed the exact-head Ubuntu, macOS and Windows assurance matrix,
  CodeQL, dependency review, workflow-policy lint and Codecov patch gate, then
  squash-merged to `main` as `622ec15d53b162916a0b1b390ec5dab6f2f6f3a7`.
- Reverified candidate manifest SHA-256
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`
  and all 94 recorded file hashes before upload.
- Published `edithatogo/nz-health-appropriations` at revision
  `9b85bac06597d4435fd078f6bed0f30bb008542b`. Fresh remote download verified
  the same manifest and all 94 entries with zero mismatch.
- Added the dataset to the HEOR collection. Independent collection readback
  returned item object ID `6a92b824597df1d081fc4108` with the manifest and
  revision recorded in its note.
- Post-publication `./scripts/validate.sh` passed with 1,215 tests, 95.55%
  coverage, 30 schemas, 20 representative documents, 9/9 parity checks, all
  mutation lanes, hygiene, supply-chain audit, licence and secret checks, and
  a validated 110-component SBOM.
