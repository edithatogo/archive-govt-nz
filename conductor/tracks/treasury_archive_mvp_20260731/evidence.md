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
