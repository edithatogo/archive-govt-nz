# Spec - Protected Production Zenodo Archive

## Status
done

## Goal
publish annual DOI snapshots only after explicit approval.

## Acceptance Criteria
- Production draft path is proven.
- Publication requires approval.
- DOI is recorded after publication.

## Evidence to Record
- Production deposition URL.
- DOI.
- Commit updating citation files.

## Evidence Recorded

- Published record: `https://zenodo.org/records/20592540`.
- DOI: `10.5281/zenodo.20592540`.
- Concept DOI: `10.5281/zenodo.20592539`.
- Workflow run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27132519663`.
- Publication occurred after explicit owner approval.
- The Zenodo related identifier now points to
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Published archive filenames remain immutable and still include the old launch
  prefix.

## Remaining Items

- Future annual snapshots should preserve the protected approval path.
- Track 27 will revisit rights metadata and evaluate `zenodraft` for future
  draft/version operations.
