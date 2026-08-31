# Specification - Separate Historical Hugging Face Corpus

## Overview

Prepare historical corpus publication as a separate Hugging Face dataset,
following the Hansard-style separation pattern and avoiding overwrite of the
live partial/API-discovery dataset.

## Functional Requirements

- Use `edithatogo/corpus-legislation-nz-historical` as the historical Hugging
  Face dataset target.
- Document that `edithatogo/corpus-legislation-nz` remains the live
  partial/API-discovery dataset.
- Confirm or create a historical Hugging Face dataset shell with root-level
  layout.
- Configure a separate repository variable such as `HF_HISTORICAL_REPO_ID`.
- Ensure historical pilots and uploads cannot write to `HF_REPO_ID` unless
  explicitly intended.

## Non-Functional Requirements

- Keep live and historical publication targets separate.
- Fail closed when historical target configuration is absent or ambiguous.
- Preserve public wording that historical publication does not imply full live
  corpus completeness.

## Acceptance Criteria

- Historical publication target is documented and separate from the live
  dataset.
- Historical dataset shell exists or has a precise creation runbook.
- Repository variables/secrets distinguish live and historical upload targets.

## Completion Evidence

- Historical target documented as
  `edithatogo/corpus-legislation-nz-historical`.
- Live target `edithatogo/corpus-legislation-nz` remains the partial/API
  discovery corpus and must not be overwritten.
- GitHub variable contract documented as
  `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`.
