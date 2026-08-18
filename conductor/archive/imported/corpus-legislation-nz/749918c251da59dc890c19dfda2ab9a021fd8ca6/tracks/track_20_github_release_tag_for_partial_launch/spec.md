# Specification - GitHub Release Tag For Partial Launch

## Overview

Create a GitHub release and tag for the approved intentional partial/API-discovery
launch while preserving public wording that the dataset is not yet proven
complete.

## Functional Requirements

- Confirm `docs/public_launch_decision.md` records launch approval and the
  scheduled-run waiver.
- Choose and create a release tag for the partial/API-discovery launch.
- Create a GitHub release on `main`.
- Update launch documentation with the real release/tag URL.
- Ensure release notes do not claim full New Zealand legislation coverage.

## Non-Functional Requirements

- Keep release wording conservative and evidence-backed.
- Preserve stable public URLs and citation expectations.
- Avoid implying that search-derived discovery proves complete coverage.

## Acceptance Criteria

- A GitHub release/tag exists for the approved partial launch.
- Launch docs record the release/tag.
- Public wording remains clear that the dataset is partial/API-discovery based.

## Completion Evidence

- GitHub release:
  `https://github.com/edithatogo/corpus-legislation-nz/releases/tag/v0.1.0-partial.20260609`.
- Tag `v0.1.0-partial.20260609` points at commit
  `3196fb415276e1d1e8edd3c394ddeac30d4485a9`.
