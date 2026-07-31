# Treasury Archive MVP Run Log

## 2026-07-31 - Planning

- Confirmed track classification: MVP / Bootstrap.
- Confirmed complete live Treasury metadata and eligible-resource capture
  boundary.
- Confirmed gated full Hugging Face and Zenodo vertical slice.
- Confirmed core Parquet, JSONL, manifest, hash, and material WARC outputs.
- Confirmed bounded OCFL, RO-Crate, and BagIt evaluation.
- Confirmed configurable fail-closed resource policy.
- Live read-only probe observed CKAN 2.10.9 and 54 Treasury datasets.
- No dataset resource payloads were downloaded during planning.
- No GitHub repository, issue, Hugging Face dataset, or Zenodo deposition was
  created during planning.

## 2026-07-31 - Task: Establish GitHub and Conductor traceability

- Marked the track in progress and committed the state transition as `5c4582d`.
- Confirmed authenticated GitHub CLI account `edithatogo`.
- Confirmed no repository named `archive-govt-nz` existed under that account.
- Created public repository `edithatogo/archive-govt-nz`.
- Added local remote `github` and pushed `main`.
- Verified the remote and local head were identical at
  `5c4582d9dc1916b05ba0305802293345b35825cf` before the task evidence commit.
- Created parent issue #1 and phase issues #2 through #11.
- Attached all ten phase issues through GitHub's native subissues API.
- Read back the parent, all ten subissues, visibility, default branch, and
  remote head.
- GitHub connector issue creation returned 403 for the new repository; used the
  authenticated CLI fallback with exact-title idempotency checks.
