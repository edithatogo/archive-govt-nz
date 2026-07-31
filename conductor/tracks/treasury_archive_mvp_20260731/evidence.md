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
