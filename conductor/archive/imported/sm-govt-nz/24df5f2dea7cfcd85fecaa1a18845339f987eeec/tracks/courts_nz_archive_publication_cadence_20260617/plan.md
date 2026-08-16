# Plan - Courts of New Zealand Archive Publication Cadence

## Phase 1: Current Behavior Audit
- [x] Task: Review `.github/workflows/archive_sources.yml`,
  `.github/workflows/publish_archives.yml`, and
  `.github/workflows/publish_zenodo_deposition.yml`.
- [x] Task: Confirm whether scheduled `Publish Archives` runs currently publish
  externally or only upload GitHub artifacts.
  - Before this track, scheduled `Publish Archives` built and uploaded GitHub
    artifacts only because `PUBLISH_ARCHIVES` was true only for manual
    `publish=true` dispatches.
  - This track changes scheduled `Publish Archives` runs to publish the
    Hugging Face rolling dataset only, leaving Zenodo under manual review.
- [x] Task: Record current Hugging Face dataset URL, Zenodo DOI, and latest
  successful publication run IDs.
  - Hugging Face: https://huggingface.co/datasets/edithatogo/courts-nz-public-notices-archive
  - Zenodo DOI: `10.5281/zenodo.20690547`
  - Publication run recorded in `conductor/archive_publication_report_20260614.json`:
    `27502440387`.

## Phase 2: Hugging Face Cadence
- [x] Task: Decide the default Hugging Face cadence for Courts of New Zealand
  archive updates.
  - Decision: weekly scheduled rolling update from `Publish Archives`.
- [x] Task: Implement a safe scheduled Hugging Face publication path or an
  explicit manual-approval gate if automatic external publishing is not wanted.
  - `Publish Archives` now supports `--publish-target huggingface`, and the
    scheduled workflow uses that target instead of publishing all external
    repositories.
- [x] Task: Add a freshness report that compares the latest archive commit with
  the latest Hugging Face publication.
  - `conductor/archive_publication_status.json` is written by
    `scripts/publish_archives.py` and committed by the workflow.

## Phase 3: Zenodo Cadence
- [x] Task: Define snapshot cadence, such as monthly, milestone, or manual-only.
  - Decision: manual release snapshot after review; monthly can be used once a
    release is reviewed, but there is no automatic Zenodo publish.
- [x] Task: Keep DOI publication behind an explicit confirmation phrase or
  release-review gate.
  - `Publish Zenodo Deposition` still requires `publish-zenodo-doi`.
- [x] Task: Record the relation between GitHub archive state, Hugging Face
  rolling dataset, and Zenodo versioned snapshots.
  - Recorded in `config/corpus_social_media_government_nz_publication_cadence.json` and
    `docs/corpus-social-media-government-nz-publication.md`.

## Phase 4: Closeout
- [x] Task: Update multi-source archive plan and project docs with final cadence.
- [x] Task: Run the relevant publication workflow in artifact-only mode and, if
  approved, one external publication run.
  - Artifact-only run captured in `conductor/archive_publication_status.json`
    (head SHA `73e9935c343e058199b9bcc6319729448d648079`, 4591 archive files,
    4213 normalized records, SHA256
    `e99c1c74e2cda3d35662cabdf19651385e54dc6770128a14a47c427fd5adc5b9`).
- [x] Task: Commit publication reports and track status.
  - Cadence config committed in `73e9935` ("Implement-Courts-NZ-archive-publication-cadence").
  - Latest status committed in `10a1b2f` ("Update archive publication status").

Current runtime status: archive capture is scheduled. Weekly `Publish Archives`
is now the Hugging Face rolling update lane; Zenodo remains a manual release
snapshot lane.
