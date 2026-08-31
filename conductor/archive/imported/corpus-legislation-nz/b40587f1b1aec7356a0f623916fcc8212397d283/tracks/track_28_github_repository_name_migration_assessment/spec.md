# Spec - GitHub Repository Name Migration Assessment

## Status
done

## Goal

Assess safe migration or reservation of the preferred corpus-nz-legislation GitHub name.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.

## Evidence Recorded

- `docs/github_repository_name_migration_assessment.md` records current GitHub
  state, target-name availability check, migration options, public-surface
  implications, pre-rename checklist, and reservation repository contract.
- Current live repository remains `edithatogo/corpus-legislation-nz`.
- Preferred target `edithatogo/corpus-nz-legislation` was not found or not
  accessible through `gh repo view`.
- No Zenodo workflow change was required by this track.
