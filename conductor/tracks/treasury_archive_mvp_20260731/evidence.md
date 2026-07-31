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
| GitHub repository | not created or verified | external write pending |
| Hugging Face publication | not requested or configured | credential and publication gate pending |
| Zenodo publication | not requested or configured | deposition and DOI gates pending |

The observed count of 54 is not a completeness constant. Implementation must
reconcile the full live scope at each run.
