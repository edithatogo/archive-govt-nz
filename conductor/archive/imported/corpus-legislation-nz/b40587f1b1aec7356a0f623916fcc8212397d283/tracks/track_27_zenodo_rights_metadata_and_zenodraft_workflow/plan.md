# Plan - Zenodo Rights Metadata And Zenodraft Workflow

## Phase 1 - Rights and metadata audit

- [x] Audit current Zenodo record license, files, creators, related identifiers, concept DOI, and version DOI.
- [x] Separate rights for repository code, docs, manifests, source text, normalized Parquet, generated metadata, and archive bundle.
- [x] Decide whether Zenodo license metadata should remain CC-BY-4.0, switch to other-open, or use another rights statement with scope notes.
- [x] Align `README.md`, `DATASET_CARD.md`, `CITATION.cff`, `NOTICE.md`, and Zenodo metadata text.

## Phase 2 - Zenodraft adoption/evaluation

- [x] Add `zenodraft` evaluation notes from `https://github.com/zenodraft/zenodraft`.
- [x] Decide between `npx zenodraft`, pinned npm install, or Docker invocation in CI.
- [x] Document Node >= 20 and npm >= 10 requirements if adopted.
- [x] Map existing `ZENODO_TOKEN` / `ZENODO_SANDBOX_TOKEN` secrets to `ZENODO_ACCESS_TOKEN` / `ZENODO_SANDBOX_ACCESS_TOKEN` only within the relevant step.
- [x] Generate local Zenodo metadata and validate it with `zenodraft metadata validate`.
- [ ] Prove sandbox draft creation or version creation with `zenodraft deposition create concept --sandbox` or `zenodraft deposition create version --sandbox <concept_id>`.
- [ ] Prove file upload with `zenodraft file add --sandbox`.
- [ ] Prove metadata update with `zenodraft metadata update --sandbox`.
- [ ] Capture prereserved DOI/details with `zenodraft deposition show prereserved --sandbox` and `zenodraft deposition show details --sandbox`.

## Phase 3 - Protected publication gate

- [x] Keep `zenodraft deposition publish` out of ordinary upload/update jobs.
- [x] Require GitHub environment protection and reviewer approval before production publish.
- [x] Record production publication evidence only after draft review.

## Verification

- [x] Metadata JSON parses.
- [x] Track is registered in `conductor/tracks.md`.
- [x] Sandbox proof and token mapping are documented before production use.

## Evidence

- Rights/zenodraft decision: `docs/zenodo_rights_metadata_zenodraft.md`.
- Metadata example: `docs/zenodo/zenodo-2026-metadata.example.json`.
- `npx --yes zenodraft metadata validate docs/zenodo/zenodo-2026-metadata.example.json` passed locally.
- Full sandbox draft/upload/update was not run in this track; it is documented
  as the required proof before replacing the Python uploader.
