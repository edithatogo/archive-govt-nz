# Treasury Archive MVP Evidence

## Planning evidence

| Evidence | State | Detail |
| --- | --- | --- |
| Product context | verified local | `conductor/index.md` and all linked setup artefacts exist |
| Git baseline | verified local | clean `main` at setup commit `dbfa534` before track creation |
| Catalogue | observed live | `https://catalogue.data.govt.nz/` |
| Action API | observed live | versioned `/api/3/action/` endpoints responded |
| CKAN version | observed live | `2.10.9` from `status_show` on 2026-07-31 |
| Treasury name | observed live | `the-treasury` |
| Treasury ID | observed live | `4d08a178-e03b-4e97-b79d-83d9a7a35744` |
| Treasury count | dated observation | 54 organisation-filtered datasets on 2026-07-31 |
| Dataset payload capture | not started | planning probes did not download resource payloads |
| GitHub repository | remotely verified | `https://github.com/edithatogo/archive-govt-nz`, public, default branch `main` |
| GitHub remote | remotely verified | local `github` remote targets the repository; pushed `main` matched local `5c4582d9dc1916b05ba0305802293345b35825cf` before this task evidence commit |
| GitHub parent issue | remotely verified | [#1 Treasury Archive MVP](https://github.com/edithatogo/archive-govt-nz/issues/1) |
| GitHub nested subissues | remotely verified | native subissues API returned phase issues #2 through #11 under parent #1 |
| Hugging Face publication | not requested or configured | credential and publication gate pending |
| Zenodo publication | not requested or configured | deposition and DOI gates pending |

The observed count of 54 is not a completeness constant. Implementation must
reconcile the full live scope at each run.

## Task evidence: Establish GitHub and Conductor traceability

- GitHub CLI authentication identified the active account as `edithatogo`.
- Connector search found no pre-existing `archive-govt-nz` repository.
- Repository creation returned
  `https://github.com/edithatogo/archive-govt-nz`.
- `gh repo view` verified `PUBLIC`, unarchived, default branch `main`.
- `git ls-remote github refs/heads/main` matched the local commit before the
  task evidence commit.
- Parent issue #1 was created with the track path, M-01 through M-19, evidence
  contract, external gates, and solo-maintainer governance.
- Phase issues #2 through #11 were created with plan and requirement references.
- The GitHub subissues API returned exactly ten children with numbers #2–#11.
- The connected GitHub app returned 403 for issue creation in the newly created
  repository, so the authenticated GitHub CLI completed the issue writes. No
  duplicates were created; exact-title checks made the fallback idempotent.

## Task evidence: Write failing package and CLI bootstrap tests

| Check | Expected red result | Observed |
| --- | --- | --- |
| Package import | `archive_govt_nz` is absent | `ModuleNotFoundError` |
| CLI contract collection | package exit-code module is absent | `ModuleNotFoundError` |
| Failure count | both bootstrap modules fail collection | 2 collection errors |

The red phase failed for the intended missing-implementation reason before any
package code or dependency manifest existed.

## Task evidence: Implement the Python 3.14 project foundation

| Evidence | State | Detail |
| --- | --- | --- |
| Runtime | verified local | CPython 3.14.6 selected by `uv` |
| Resolution | verified local | `uv lock --python 3.14` resolved 14 packages |
| Package | verified local | distribution metadata and import version agree |
| CLI help | verified local | identifies `archive-govt-nz` and `version`; exit 0 |
| CLI JSON | verified local | schema `archive-govt-nz.cli/v1`; deterministic compact JSON; exit 0 |
| Exit states | verified local | six unique documented values from 0 through 50 |
| Focused tests | passed local | 5 passed in 1.84 seconds |
| Build | passed local | sdist and `py3-none-any` wheel built from locked sources |
| Hosted CI | not configured | Phase 1 assurance and workflow tasks remain open |
| Archive capture | not started | no catalogue metadata or resource payload was captured |
| Publication | not started | no Hugging Face or Zenodo action occurred |

Changed implementation files are `pyproject.toml`, `uv.lock`, `README.md`, and
`src/archive_govt_nz/`. Cyclopts is recorded in `conductor/tech-stack.md`.
Configuration currently accepts an explicit state directory only; environment
and file formats will be introduced with typed schema and precedence tests in a
later bounded task.

## Task evidence: Establish the repository-wide assurance harness

| Stage | State | Evidence |
| --- | --- | --- |
| Lock | passed local | `uv lock --check`; 26-package resolved environment |
| Format | passed local | Ruff reported 31 files already formatted |
| Lint | passed local | Ruff full ruleset reported all checks passed |
| Types | passed local | strict Pyright: 0 errors, 0 warnings, 0 information |
| Tests | passed local | 14 tests passed in 4.93 seconds |
| Coverage | passed local | 50/50 statements and 6/6 branches; 100% overall |
| Property testing | passed local | Hypothesis generated exit-state invariant examples |
| Schema | passed local | Draft 2020-12 CLI envelope schema and fixture validated |
| Fail-closed gate | passed local | first nonzero stage stops later stages and preserves status |
| Hosted CI | not configured | supply-chain and CI tasks remain open |

The only coverage omission is `src/archive_govt_nz/__main__.py`, a declarative
two-line module wrapper already exercised through subprocess CLI contract tests.
This is narrow and does not contain decision logic.

## Task evidence: Establish supply-chain and repository controls

| Control | State | Evidence |
| --- | --- | --- |
| Dependency resolution | passed local | locked environment contains 69 packages |
| Vulnerability audit | passed live lookup | pip-audit 2.10.1 via OSV: no known vulnerabilities |
| Licence inventory | passed local | no unknown, GPL, or AGPL terms in installed inventory |
| Secret scan | passed local | zero candidates in bounded source scope |
| SBOM generation | passed local | reproducible CycloneDX 1.6 JSON; 69 components |
| SBOM validation | passed local | strict CycloneDX schema validator returned no error |
| Governance documents | verified local | security, contribution, authorship, AI, and Apache-2.0 files present |
| Rust policy | verified local | no Rust code; adoption requires measured template evidence |
| Full gate | passed local | all ten stages; 17 tests; 100% measured line and branch coverage |
| Hosted security | not configured | CodeQL, GitHub secret scanning, attestations, and Actions remain later tasks |

Generated audit, licence, secret-scan, and SBOM receipts are under ignored
`build/`. They describe the current local environment and are not committed,
uploaded, or remotely verified. The timed-out PyPI advisory attempt is a
network-route limitation, not a vulnerability result; OSV supplied the recorded
successful lookup.

## Phase 1 checkpoint

| Evidence | State | Detail |
| --- | --- | --- |
| Full local gate | passed local | ten stages; 17 tests; 100% measured line and branch coverage |
| Isolated install | passed local | locked Python 3.14 environment installed 69 packages |
| Isolated CLI | passed local | help identified product and version command |
| Isolated tests | passed local | 17 tests in 10.60 seconds; 100% measured coverage |
| Distribution build | passed local | `0.1.0` sdist and `py3-none-any` wheel |
| GitHub repository | remotely verified | public, unarchived, default branch `main` |
| Remote ref | remotely verified | `github/main` equals local `45420f3c153b95628fabfd8de83f92a3f5054fba` before checkpoint commit |
| Issue hierarchy | remotely verified | parent #1 plus native subissues #2 through #11 |
| Phase 1 issue | pending close | close only after checkpoint commit push and readback |
| Hosted CI | not implemented | planned Phase 7 work; no hosted-pass claim |
| Archive/publication | not started | no source payload, Hugging Face, or Zenodo action |

The paired machine-readable checkpoint is
`evidence/phase-1-checkpoint.json`.

## Task evidence: Continuous autonomous Conductor execution

| Evidence | State | Detail |
| --- | --- | --- |
| Human policy | verified local | `conductor/autonomy.md` |
| Machine policy | schema validated | `archive-govt-nz.conductor-autonomy/v1` |
| Continuation | verified local | automatic across tasks, phases, checkpoints, reviews, and tracks |
| Decision contract | verified local | 2–4 options, recommendation first, rationale, evidence, blocking scope |
| Recovery | verified local | three distinct attempts; changed hypothesis required |
| Resumability | verified local | repository, Conductor, Git, remote, and issue state reconciled |
| Isolation | policy verified | conditional `codex/` branch/worktree; upstream draft code not adopted |
| Focused tests | passed local | 4 tests |
| Schema suite | passed local | 2 schemas and representative documents |
| Full repository gate | passed local/live | 10 stages; 21 tests; 100% measured coverage; OSV clean |
| GitHub traceability | remotely verified | native parent subissue [#12](https://github.com/edithatogo/archive-govt-nz/issues/12) |

Upstream observation is recorded in
`conductor/upstream-evaluation.md`. Draft PRs #86 and #161 are research inputs,
not installed dependencies or supported-feature claims.

## Task evidence: Write failing CKAN envelope and capability tests

| Contract | Expected red result | Observed |
| --- | --- | --- |
| Envelope classification | CKAN module absent | `ModuleNotFoundError` |
| Sensitive-value redaction | CKAN module absent | `ModuleNotFoundError` |
| Collection outcome | both contract modules fail | 2 collection errors |

No live request, source payload, credential, or publication action occurred.
The next task owns the smallest bounded implementation that makes these
contracts green.

## Task evidence: Implement the CKAN envelope and redaction kernel

| Evidence | State | Detail |
| --- | --- | --- |
| Focused tests | passed local | 19 tests in 0.92 seconds |
| Critical coverage | passed local | 100% line and branch for CKAN modules |
| Strict typing | passed local | 0 errors |
| Envelope semantics | verified local | HTTP and CKAN states classified independently |
| Retry semantics | verified local | only explicit transient statuses and timeouts retryable |
| Redaction | verified local | five sensitive values removed; safe evidence retained |
| Source immutability | verified local | input document unchanged |
| Live CKAN | not accessed | HTTP client remains the next bounded tasks |

## Task evidence: Write failing bounded CKAN HTTP client tests

| Contract | Expected red result | Observed |
| --- | --- | --- |
| Client import | bounded client module absent | `ModuleNotFoundError` |
| Collection outcome | implementation cannot be imported | 1 collection error |
| Retry controls | deterministic injected schedule | 3 attempts; 0.5/1.0 second contract |
| Receipt controls | exact bytes and bounded safe metadata | test contract only |
| Runtime dependencies | current stable Python 3.14-compatible releases | lock resolved 79 packages |

The red phase failed at the intended missing implementation boundary. The
contracts use only an in-memory transport; they do not establish live CKAN,
Treasury scope, archive capture, or publication evidence.

## Task evidence: Implement the bounded CKAN HTTP client

| Evidence | State | Detail |
| --- | --- | --- |
| Focused contracts | passed local | 18 tests |
| Critical coverage | passed local | 165/165 statements; 40/40 branches |
| Complete CKAN suite | passed local | 37 tests |
| Complete repository suite | passed local | 58 tests; 100% measured coverage |
| Static assurance | passed local | Ruff and strict Pyright: zero findings |
| Source secret scan | passed local | zero candidates |
| Streaming bound | verified local | declared and incremental over-limit paths fail closed |
| Retry bound | verified local | terminal, exhaustion, timeout, network, and unknown paths |
| Receipt redaction | verified local | allowlisted headers; no cookie or exception detail |
| Live CKAN | not accessed | deterministic in-memory transport only |

The implementation retains exact received response bytes under identity
encoding and records their SHA-256 separately from the parsed CKAN envelope.
It does not claim that the catalogue supports a particular CKAN version until a
later bounded live observation is captured and hashed.

## Task evidence: Write failing Treasury discovery tests

| Contract | Expected red result | Observed |
| --- | --- | --- |
| Discovery import | Treasury discovery module absent | `ModuleNotFoundError` |
| Collection outcome | implementation cannot be imported | 1 collection error |
| Scope baseline | live count drives pagination | no hard-coded 54 acceptance |
| Raw evidence | organisation and every search page retained | test contract only |
| Reconciliation | duplicate, missing ID, premature exhaustion terminal | test contract only |

The red phase uses typed in-memory Action observations. It proves neither the
current number of Treasury datasets nor live catalogue completeness.

## Task evidence: Implement complete Treasury discovery

| Evidence | State | Detail |
| --- | --- | --- |
| Focused contracts | passed local | 20 tests |
| Critical coverage | passed local | 138/138 statements; 24/24 branches |
| Complete repository suite | passed local | 78 tests; 100% measured coverage |
| Static assurance | passed local | Ruff and strict Pyright: zero findings |
| Source secret scan | passed local | zero candidates |
| Organisation identity | verified fixture | slug, stable ID, name, and title required |
| Pagination | verified fixture | sorted starts, live count drift, progress reconciliation |
| Raw evidence | verified fixture | exact bytes, hash, time, start, and page IDs |
| Paired reports | verified fixture | canonical JSON plus Markdown limitation report |
| Live Treasury scope | not observed | bounded live checks are the next task |

The discovery model represents a genuine zero-dataset result and retains
optional CKAN labels without using them as identity. It refuses to report
completeness when page ordering, identifiers, or live counts cannot be
reconciled.

## Task evidence: Add bounded live read-only contract checks

| Evidence | State | Detail |
| --- | --- | --- |
| Capability | observed local/live | CKAN 2.10.9; Action API v3 |
| Catalogue identity | observed local/live | `https://catalogue.data.govt.nz` |
| Treasury identity | observed local/live | stable ID `4d08a178-e03b-4e97-b79d-83d9a7a35744` |
| Treasury scope | reconciled local/live | 54 unique datasets |
| Pagination | reconciled local/live | starts 0, 25, 50; results 25, 25, 4 |
| Count stability | observed local/live | reported 54 on all three pages |
| Raw receipts | hashed local | 5 responses; about 277 KiB |
| Scope report | hashed local | SHA-256 `bb72d7fb...75f8414c` |
| Evidence writer | passed deterministic | atomic raw and paired report promotion |
| Licence inventory | passed local | explicit Artistic alternative for `text-unidecode` 1.3 |
| Secret scan | passed local | checksum receipt lines classified separately |
| SBOM | passed local | validated CycloneDX 1.6; 79 components |
| Resource payloads | not requested | metadata-only operation |
| Hosted schedule | not configured | planned Phase 7 work |

The authoritative bounded summary is
`evidence/phase-2-live-observation.json`; its Markdown companion states the
same limitations. Exact raw responses are intentionally not committed and have
not been uploaded or remotely verified.

## Phase 2 checkpoint

| Evidence | State | Detail |
| --- | --- | --- |
| Full repository gate | passed local/live | all ten stages in 103.3 seconds |
| Tests | passed local | 80 |
| Coverage | passed local | 476/476 statements; 100/100 branches |
| Schemas | passed local | 2 schemas and representative documents |
| Vulnerabilities | passed live lookup | OSV: no known vulnerabilities |
| Licences | passed local | 79-package environment; documented alternative |
| Secrets | passed local | zero candidates |
| SBOM | passed local | CycloneDX 1.6; 79 components |
| Live capability | observed local/live | CKAN 2.10.9; Action API v3 |
| Live Treasury scope | reconciled local/live | 54 unique datasets across 3 pages |
| Raw provenance | retained local | five exact ignored files with SHA-256 |
| Remote ref before checkpoint | remotely verified | `github/main` = `d04aeccf...ab80a1` |
| Resource capture | not started | Phase 3–6 controls remain |
| Publication | not started | Hugging Face and Zenodo gates remain |

The paired machine-readable checkpoint is
`evidence/phase-2-checkpoint.json`.

## Task evidence: Define versioned archive schemas

| Evidence | State | Detail |
| --- | --- | --- |
| Schema catalogue | specified | 10 versioned record kinds |
| Relationship model | specified | Mermaid source-to-publication graph |
| Common invariants | specified | IDs, UTC, state, evidence, hashes, redaction |
| Object roles | specified | originals and derivatives remain distinct |
| Publication gates | specified | prepared/uploaded/verified/released separated |
| Compatibility | specified | immutable published versions; fail-closed readers |
| Migration | specified | non-destructive receipt-bearing transformation |
| Canonical bytes | specified | deterministic UTF-8 JSON plus newline |
| Runtime schemas | not implemented | next red/green tasks |

## Task evidence: Write failing schema and invariant tests

| Contract | Expected red result | Observed |
| --- | --- | --- |
| Record module | archive record API absent | `ModuleNotFoundError` |
| Collection outcome | implementation cannot be imported | 1 collection error |
| Schema catalogue | all 10 v1 kinds executable | test contract only |
| Common invariants | ID, UTC, closed properties | test contract only |
| State invariants | object role and publication evidence | test contract only |
| Canonicalization | stable JSON; NaN terminal | test contract only |

The red phase fails only at the absent implementation boundary. Existing CKAN
records and live evidence remain unchanged.

## Task evidence: Implement typed domain models and schemas

| Evidence | State | Detail |
| --- | --- | --- |
| Typed records | implemented | common header plus 10 record kinds |
| Runtime validation | passed local | strict Draft 2020-12 with format checks |
| Generated schemas | passed local | 10 immutable files match typed catalogue |
| Repository schema gate | passed local | 12 schemas; 2 representative documents |
| Focused contracts | passed local | 31 tests |
| Critical coverage | passed local | 189/189 statements; 10/10 branches |
| Complete suite | passed local | 121 tests; 100% measured coverage |
| Static assurance | passed local | Ruff and strict Pyright: zero findings |
| Secret scan | passed local | zero candidates |
| Archive payloads | not created | schemas and synthetic records only |

## Task evidence: Define the fail-closed resource policy

| Evidence | State | Detail |
| --- | --- | --- |
| Policy version | specified | `resource-policy/v1` |
| Network bounds | specified | schemes, redirects, time, bytes, retries |
| Archive safety | specified | decompression, members, ratios, paths |
| Type evidence | specified | independent magic/content inspection |
| Rights states | specified | eligible, restricted, unavailable, quarantine |
| Exception gate | specified | bounded, expiring, auditable, no destructive bypass |
| Property evaluator | not implemented | next red/green task |
| Resource payloads | not accessed | metadata and policy documentation only |

## Task evidence: Write failing resource-policy property tests

| Contract | Expected red result | Observed |
| --- | --- | --- |
| Policy module | resource evaluator absent | `ModuleNotFoundError` |
| URL safety | unsafe schemes and credentials terminal | test contract only |
| Redirect safety | downgrade and loop terminal | test contract only |
| Rights/limits | restricted, oversized, retryable explicit | test contract only |
| Type/archive | conflict and bomb quarantine | test contract only |
| Outcome closure | every candidate receives a disposition | test contract only |
| Canonical receipt | deterministic newline JSON | test contract only |

The red phase fails only at the intended absent evaluator boundary.

## Task evidence: Implement resource-policy evaluation

| Evidence | State | Detail |
| --- | --- | --- |
| Policy evaluator | passed local | pure typed `resource-policy/v1` kernel |
| Dispositions | passed local | 7 explicit states |
| Critical coverage | passed local | 127/127 statements; 44/44 branches |
| Full suite | passed local | 137 tests; 100% measured coverage |
| URL/redirect bounds | passed local | scheme, credentials, host, loop, count |
| Rights/size/type/archive | passed local | restricted, oversized, quarantine, retry |
| Filename handling | passed local | sanitized metadata; no path construction |
| Static assurance | passed local | Ruff and strict Pyright: zero findings |
| Secret scan | passed local | zero candidates after fixture redaction |
| Mutation testing | passed local | 8/8 targeted critical mutants killed |
| Payload access | none | evaluator remains side-effect free |

Mutation hardening is now passed: the integrated gate killed 8/8 targeted
critical-policy mutants in isolated temporary package copies. Native mutmut was
not used because its Windows/WSL requirement is unavailable; mutatest was not
used because its Python 3.14 runtime path fails before mutation execution.

## Phase 7 hosted CI checkpoint - 2026-08-01

| Evidence | State | Detail |
| --- | --- | --- |
| Local aggregate gate | passed | 179 tests; 96.78% coverage; Ruff/Pyright; schemas; 11/11 mutants; supply-chain controls |
| Clean-runner fixtures | passed | release package, DuckDB query, and attestation tests generate isolated inputs |
| Hosted Linux CI | passed | GitHub Actions run `30669731935`; head `b0fe541e7077c96e4817767ab5e0e168d32453bd` |
| Codecov | passed | tokenless OIDC upload succeeded in the hosted run |
| Secret scan | passed | receipt hashes/revisions narrowly excluded by field name; no candidates |
| Action runtime warning | observed | pinned actions target Node.js 20 and are currently forced to Node.js 24; upstream pin refresh remains warranted |

## Zenodo integration checkpoint - 2026-08-01

| Evidence | State | Detail |
| --- | --- | --- |
| Environment credential gate | passed | Missing `ZENODO_TOKEN` returns `credential_missing`; token is never included in errors or receipts |
| Draft/upload/reconcile flow | passed | Injected transport test covers draft creation, multipart upload, and read-back state |
| DOI publication gate | passed | Publication requires explicit DOI confirmation and rejects mismatches |
| Network boundary | implemented | HTTPS default, bounded timeout, stable redacted transport errors |
| Remote deposition | unchanged | Existing DOI `10.5281/zenodo.21728726` remains authoritative; adapter tests do not create a new record |
| Transport bounds | passed | 256 MiB upload cap and 4 MiB response cap; oversized upload rejected before transport |

## Phase 9 reconciliation and recovery checkpoint - 2026-08-01

| Evidence | State | Detail |
| --- | --- | --- |
| Local/Zenodo package hash | matched | `472fe842...21a6b7` matches the published receipt |
| Hugging Face revision | verified | `9406a3b0...c30dbae0` |
| Zenodo DOI | verified | `10.5281/zenodo.21728726` |
| Remote recovery receipt | verified | file size and Zenodo checksum recorded |
| Recovered tar closure | verified | raw, object, and derivative layers present; member paths safe |

## M-14 recovery simulation checkpoint - 2026-08-01

| Evidence | State | Detail |
| --- | --- | --- |
| Fault boundaries | passed deterministic simulation | six interruption stages exercised |
| Restart outcome | passed deterministic simulation | all resources captured after resume |
| Duplicate prevention | passed deterministic simulation | zero duplicate objects |
| Unchanged rerun | passed deterministic simulation | repeated run remains unchanged |
| Production-path recovery | open | simulation still needs coupling to capture, object store, and ledger integration |

## M-06 secure-source resolution checkpoint - 2026-08-01

| Evidence | State | Detail |
| --- | --- | --- |
| HTTPS alternative ordering | passed | explicit secure alternatives are retained in deterministic order |
| HTTP handling | passed | HTTP is converted only to an HTTPS probe candidate; it is never accepted directly |
| Tombstone fallback | passed | no secure candidate produces `tombstone-required` |
| Live alternative probing | open | source-level 403/non-HTTPS outcomes still require bounded re-probe evidence |

## Phase 10 acceptance checkpoint - 2026-08-01

| Acceptance state | gated-incomplete |
| --- | --- |
| Must requirements verified | 15/19 |
| Must requirements partial | M-09, M-12 |
| Must requirements blocked | M-06 |
| Evidence | `evidence/phase-10-acceptance.json` |
| Publication claim | No MVP-complete or complete-source-capture claim permitted |

## Phase 3 object-store assurance slice - 2026-08-10

| Evidence | State | Detail |
| --- | --- | --- |
| Object-store negative paths | passed | Invalid chunks, inconsistent deduplication receipts, missing objects, and unreadable objects are classified fail-closed |
| Critical object-store coverage | passed | 100% line and branch coverage; 10 focused tests |
| Schema and policy/object gates | passed | 77 focused tests; 12 schemas and 2 representative documents validated |
| Mutation receipt | prior evidence | Existing 8/8 policy mutants and 3/3 version mutants remain recorded; the current aggregate invocation timed out before emitting a new receipt |
| Phase checkpoint | open | Checkpoint bookkeeping remains pending; no capture, rights, or publication gate was bypassed |

## Phase 3 checkpoint closure - 2026-08-10

| Evidence | State | Detail |
| --- | --- | --- |
| Resource-policy mutation | passed | 8/8 targeted mutants killed |
| Versioning mutation | passed | 3/3 targeted mutants killed |
| Paired checkpoint receipts | recorded | `evidence/phase-3-checkpoint.json` and `.md` |
| Scope | local-only | No restricted payload, rights, or external publication gate changed |

## Phase 4 ledger/versioning contract slice - 2026-08-10

| Evidence | State | Detail |
| --- | --- | --- |
| Ledger persistence | passed | 5 transactional ledger tests; all core entity relationships exercised |
| Disappearance tombstone | passed | Explicit `source_disappeared` reason and preserved previous fingerprint |
| Policy-change tombstone | passed | Explicit `policy_changed` reason and preserved previous fingerprint |
| Static assurance | passed | Ruff and strict Pyright passed for ledger/versioning contracts |

## Manifest receipts and execution context - 2026-08-10

| Evidence | State | Detail |
| --- | --- | --- |
| Transformation receipts | passed | Stable receipt IDs and deterministic ordering |
| Validation receipts | passed | Validation outcomes remain distinct from publication state |
| Publication receipts | passed | Prepared/remote states remain evidence fields, not implicit side effects |
| Execution context | passed | Software, environment/SBOM, parameters, rights, and limitations are preserved |
| Provenance contracts | passed | 6 focused tests; Ruff and strict Pyright passed |

## 2026-08-10 — Preservation packaging adoption decision

| Evidence | State | Detail |
| --- | --- | --- |
| RO-Crate | adopted bounded profile | Provenance envelope only; immutable object and manifest references required |
| BagIt | release-boundary profile | Payload manifests must verify before Zenodo upload |
| OCFL | deferred | Requires representative corpus, conformance fixtures, and workload evidence |
| Conformance claims | bounded | No unsupported full-standard conformance claim made |

## 2026-08-10 — Bounded capture attempt receipts

| Evidence | State | Detail |
| --- | --- | --- |
| Attempt receipts | passed | Typed redacted receipts cover redirects, captures, bounded status failures, validators, size, timeout, and transport outcomes |
| Capture contracts | passed | 12 focused tests |
| Sensitive URL handling | passed | Query credentials are redacted in receipts |
| Remaining bounds | open | Decompression, ranges, quarantine, and batch-level concurrency/storage evidence remain pending |
