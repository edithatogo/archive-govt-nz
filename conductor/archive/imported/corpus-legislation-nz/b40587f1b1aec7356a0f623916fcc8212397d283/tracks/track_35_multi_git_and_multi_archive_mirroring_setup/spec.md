# Specification - Multi-Git and Multi-Archive Mirroring

## Overview
This track implements multi-git repository mirroring and backup publishing strategies for the `corpus-legislation-nz` pipeline to guarantee durability and prevent censorship or single-point-of-failure repository/dataset takedowns.

## Requirements
1. **Multi-Git Mirroring**: Automatically push codebase updates to secondary Git remotes (GitLab and Codeberg) on every push to the canonical branches.
2. **Multi-Archive Datasets**: Establish redundant archiving. Maintain Hugging Face as the canonical live dataset repository, Zenodo as the immutable citation and snapshot repository, and OSF as a convenience mirror and review repository.

## Acceptance Criteria
- `.github/workflows/mirror_sync.yml` exists and triggers on pushes to main/master branches.
- Workflow successfully executes dry-run or bypasses when credentials are empty.
- Workflow supports multiple secondary SSH remotes through newline-separated
  `GIT_MIRROR_URLS`, while retaining single-remote `GIT_MIRROR_URL`
  compatibility.
- Mirror setup documentation identifies the required GitHub secrets and live
  verification commands without storing secret values in the repository.
- Multi-archive setup covers Hugging Face, Zenodo, and the OSF optional mirror policy (`docs/osf-optional-mirror-policy.md`).
