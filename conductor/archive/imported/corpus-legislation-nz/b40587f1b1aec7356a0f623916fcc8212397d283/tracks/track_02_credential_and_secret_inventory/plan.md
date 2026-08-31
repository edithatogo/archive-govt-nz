# Plan - Credential And Secret Inventory

## Tasks
- [x] Confirm `NZ_LEGISLATION_API_KEY` exists and can call the NZ Legislation API.
- [x] Confirm `HF_TOKEN` exists and has write access only to the intended Hugging Face dataset repository where possible.
- [x] Confirm `HF_REPO_ID` is final.
- [x] Confirm `ZENODO_TOKEN` exists.
- [x] Decide whether production Zenodo uses a separate token and required reviewer environment.
- [x] Store GitHub secrets: `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `ZENODO_TOKEN`.
- [x] Store GitHub variables: `HF_REPO_ID`, `NZLC_SEARCH_TERMS`, `NZLC_SEARCH_FIELD`, `NZLC_SEARCH_SORT_BY`, `NZLC_LEGISLATION_TYPES`, `ARCHIVE_CREATORS_JSON`, and archive metadata.
- [x] Run `uv run nzlc doctor` locally or through GitHub Actions.

## Current blocker

- `NZ_LEGISLATION_API_KEY` was supplied by the user and validated process-locally without writing the value to repo files.
- GitHub repository created and remote configured: `https://github.com/edithatogo/corpus-legislation-nz`.
- GitHub variables are configured, including corrected `ARCHIVE_CREATORS_JSON` without recording its value here.
- `HF_TOKEN`, `ZENODO_TOKEN`, and `NZ_LEGISLATION_API_KEY` are present as GitHub repository secrets.
- `HF_REPO_ID` is configured as a GitHub variable: `edithatogo/corpus-legislation-nz`.
- GitHub Actions doctor run `27125139848` passed on the PR branch after validating NZ API, Hugging Face dataset, and Zenodo production connectivity.
