# Spec - Zenodo Sandbox Archive

## Status
done

## Goal
prove annual immutable archiving without publishing to production.

## Acceptance Criteria
- Sandbox draft is created or updated.
- Archive, manifest, and checksum files are present.
- No production publication occurs.

## Evidence to Record
- Sandbox deposition URL.
- Archive filename and checksum.
- Workflow run URL if performed in GitHub Actions.

## Evidence Recorded

- Local environment presence check on 2026-06-07:
  - `ZENODO_TOKEN`: absent.
  - `ZENODO_API_URL`: absent.
  - `ARCHIVE_CREATORS_JSON`: absent.
  - `NZLC_OUTPUT_DIR`: absent.
  - `HF_REPO_ID`: absent.
- Local data/archive check on 2026-06-07:
  - `data/`: absent.
  - `dist/archive`: absent.
- Local doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `ZENODO_TOKEN`: warning, not configured.
  - `ARCHIVE_CREATORS_JSON`: warning, not configured.
  - `output_dir`: `data`.
- Archive and upload code path:
  - `uv run nzlc archive --year <year> --output-dir dist/archive` builds a `.tar.zst` archive where supported, otherwise `.tar.gz`, plus manifest and SHA256 sums.
  - `uv run nzlc zenodo-upload --year <year> --archive-dir dist/archive` requires `ZENODO_TOKEN` and `ARCHIVE_CREATORS_JSON`.
  - The Zenodo client calls `delete_duplicate_named_files` before uploading files, so duplicate-name replacement is implemented in the client path.
- GitHub workflow path:
  - `.github/workflows/annual_zenodo_archive.yml` supports manual sandbox runs with `use_sandbox=true` and `publish=false`.
  - No workflow run URL exists because there is no configured remote GitHub repository or live sandbox token.

## Blocked Items

- Cannot build a meaningful annual archive until a corpus exists under `data/`.
- Cannot upload to Zenodo sandbox until `ZENODO_TOKEN`, `ARCHIVE_CREATORS_JSON`, and the sandbox API URL are configured.
- Cannot verify sandbox draft URL, archive checksums in Zenodo, or duplicate-file replacement behavior until a sandbox draft upload succeeds.
- Cannot produce a GitHub workflow run URL until the repository is pushed and Actions secrets/variables are configured.
