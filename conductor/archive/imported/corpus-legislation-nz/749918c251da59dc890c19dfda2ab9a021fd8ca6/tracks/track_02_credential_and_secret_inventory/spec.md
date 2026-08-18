# Spec - Credential And Secret Inventory

## Status
done

## Goal
confirm all credentials and GitHub variables required for live corpus operations are present, scoped correctly, and stored in the right place.

## Acceptance Criteria
- `nzlc doctor` passes without exposing secret values.
- GitHub Actions has the required secrets and variables.
- Zenodo production publication remains approval-gated.

## Evidence to Record
- Redacted `nzlc doctor` result.
- GitHub repository variable names, not values.
- GitHub environment names and protection status.

## Evidence Recorded

- Local credential presence check on 2026-06-02:
  - `NZ_LEGISLATION_API_KEY`: supplied by user for process-local validation; value not written to repo files.
  - `HF_TOKEN`: absent.
  - `HF_REPO_ID`: absent.
  - `ZENODO_TOKEN`: absent.
  - `ARCHIVE_CREATORS_JSON`: absent.
  - Optional search/archive variables checked in the local environment: absent.
- Local `nzlc doctor` result:
  - Initial local-only run before key supply reported `NZ_LEGISLATION_API_KEY`: warning, not configured.
  - Process-local network run after key supply reported `NZ_LEGISLATION_API_KEY`: true.
  - NZ API reachable with one-row sample search; `sample total=19670`.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `ZENODO_TOKEN`: warning, not configured.
  - `ARCHIVE_CREATORS_JSON`: warning, not configured.
  - `output_dir`: `data`.
- GitHub CLI:
  - Authenticated as `edithatogo`.
  - `gh secret list` failed with `no git remotes found`.
- Git repository:
  - Isolated local repository exists.
  - No GitHub remote is configured yet.
- Base repository / GitHub cross-check on 2026-06-02:
  - Parent Git root resolves to `C:/Users/60217257/OneDrive - Flinders`.
  - Obvious local base env file found: `.env.example` only; the file is OneDrive offline and no usable local `.env` credential file was found in bounded scans.
  - Documented default GitHub repo `edithatogo/corpus-legislation-nz` is not resolvable by the authenticated GitHub account.
  - Likely base GitHub repo `edithatogo/nz-legislation` is accessible.
  - `edithatogo/nz-legislation` repo secrets contain only `CODECOV_TOKEN` and `NPM_TOKEN`; no `NZ_LEGISLATION_API_KEY`.
  - `edithatogo/nz-legislation` repo variables contain only `ENABLE_AUTOMATED_NPM_PUBLISH`; no NZ legislation corpus variables.
  - `edithatogo/nz-legislation` environments are `github-pages`, `prerelease`, and `stable`; environment secrets and variables are empty.
- VUW Outlook mailbox cross-check on 2026-06-02:
  - Outlook Web search used authenticated VUW account `mordaudy@staff.vuw.ac.nz`.
  - Found PCO announcement from `andrew.jacombs@pco.govt.nz`, subject `New Legislation API available now`, dated 2026-02-11.
  - Found PCO acknowledgement thread, subject `API Key`, dated 2026-03-26.
  - Searches for `NZ_LEGISLATION_API_KEY`, `API key legislation`, `X-Api-Key`, `api_key`, and `pco.govt.nz key` did not locate an issued API key value.
  - The official API docs state authentication uses `api_key` or `X-Api-Key` and missing/invalid keys return `401`.
- Zenodo production decision:
  - Use `zenodo-sandbox` for test drafts.
  - Use `zenodo-production` with required reviewers for production drafts/publication.
  - Prefer a separate production `ZENODO_TOKEN` stored as an environment-scoped secret.
  - Keep production publication opt-in with `publish=true`.

## Blocked Items

- `NZ_LEGISLATION_API_KEY` has been supplied and validated process-locally, but it is not stored in GitHub secrets yet.
- GitHub repository created on 2026-06-07: `https://github.com/edithatogo/corpus-legislation-nz`.
- Git remote configured as `origin`.
- GitHub variables configured: `HF_REPO_ID`, `DATA_DIR`, `NZLC_SEARCH_TERMS`, `NZLC_SEARCH_FIELD`, `NZLC_SEARCH_SORT_BY`, `NZLC_LEGISLATION_TYPES`, `ARCHIVE_CREATORS_JSON`, `ARCHIVE_TITLE`, `ARCHIVE_LICENSE`, `ARCHIVE_PUBLISH`, `ZENODO_API_URL`, and `ZENODO_SANDBOX_API_URL`.
- GitHub secrets are still absent: `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `ZENODO_TOKEN`.
- Cannot confirm Hugging Face write access until `HF_TOKEN` is supplied.
- Cannot confirm Zenodo sandbox access until `ZENODO_TOKEN` is supplied.
