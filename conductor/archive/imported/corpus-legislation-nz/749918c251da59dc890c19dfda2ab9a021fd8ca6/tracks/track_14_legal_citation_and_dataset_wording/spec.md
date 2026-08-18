# Spec - Legal, Citation, And Dataset Wording

## Status
done

## Goal
keep public statements accurate about corpus coverage, licensing, and incorporated-by-reference material.

## Acceptance Criteria
- Public docs make no unsupported completeness claim.
- License and citation wording are internally consistent.
- Zenodo and Hugging Face metadata align.

## Evidence to Record
- Reviewed files.
- Reviewer notes.
- Metadata commit SHA.

## Evidence Recorded

- Files reviewed and updated on 2026-06-07:
  - `README.md`
  - `DATASET_CARD.md`
  - `CITATION.cff`
  - `scripts/init_huggingface_dataset.py`
- Reviewer notes:
  - Discovery status is now stated as not proven complete unless reconciled against an authoritative inventory.
  - Current public wording distinguishes API-first/search-based pipeline readiness from proven corpus completeness.
  - Code license is separated from legislation/source-content reuse status.
  - Official NZ Legislation copyright/disclosure pages were checked on 2026-06-07 and support Crown copyright / Creative Commons attribution wording.
  - Caveats now cover incorporated-by-reference material, third-party material, agency website text, logos, emblems, and non-legislative linked content.
  - Citation guidance now distinguishes live Hugging Face use from fixed-version annual Zenodo snapshots.
  - Zenodo metadata currently defaults `ARCHIVE_LICENSE` to `cc-by-4.0`; this should be reviewed before a real public archive to ensure it does not imply relicensing of source legislation text or third-party material.
- Current metadata result:
  - No metadata commit SHA exists yet because this working tree has not been committed.
  - Live Hugging Face dataset card and Zenodo metadata cannot be verified until Tracks 03, 08, 12, and 13 are unblocked.

## Blocked Items

- Cannot record final metadata commit SHA until the current wording changes are committed.
- Cannot confirm live Hugging Face metadata alignment until the dataset repository exists and its card is generated/read back.
- Cannot confirm Zenodo metadata alignment until a sandbox or production draft is created and reviewed.
