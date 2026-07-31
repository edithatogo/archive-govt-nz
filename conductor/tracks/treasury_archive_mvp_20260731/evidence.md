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
