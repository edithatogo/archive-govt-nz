# Spec - Monthly Full Reconciliation

## Status
ready

## Goal
keep the corpus complete over time, not only during the first bootstrap.

## Acceptance Criteria
- Reconciliation cadence is documented.
- Seed changes are reviewed.
- Coverage deltas are explained in `latest_changes.json` or a maintenance note.

## Evidence to Record
- Reconciliation date.
- Added or removed work IDs.
- Coverage deltas.

## Evidence Recorded

- Reconciliation cadence documented on 2026-06-07:
  - `docs/reconciliation_runbook.md` defines monthly reconciliation after first full bootstrap.
  - The runbook allows quarterly reconciliation only after a recorded maintainer decision.
  - `docs/maintenance_runbook.md` now points monthly maintenance to the full reconciliation procedure.
- 2026-06-21 repo-side reconciliation guard:
  - `.github/workflows/monthly_full_reconciliation.yml` has safe scheduled-run
    defaults for baseline seed path, max works, request pacing, and disk budget.
  - Confirmed Hugging Face publication fails closed in the reconciliation
    workflow; publication must use Track 08 after reviewing reconciliation
    artifacts.
- Local inventory/output check updated on 2026-06-21:
  - `seeds/work_ids.txt`: present as the Track 04 search-derived seed
    inventory and usable as the operational baseline for reconciliation.
  - `data/manifests/coverage_report.json`: absent locally for a reviewed full
    corpus.
- Current reconciliation result:
  - No reconciliation run was performed.
  - Added work IDs: none.
  - Removed work IDs: none.
  - Coverage deltas: unavailable because no full corpus coverage report exists.

## Blocked Items

- Cannot complete full seed, discovery, and coverage-output comparison until a
  reviewed full corpus coverage report exists.
- Cannot promote newly discovered work IDs into `seeds/work_ids.txt` without a
  reviewed reconciliation artifact and provenance.
- Cannot rerun a reviewed full sync in staged batches until Track 07 produces a
  completed full-bootstrap artifact.
- Cannot explain coverage deltas in `latest_changes.json` or a maintenance note until a real full reconciliation run has outputs to compare.
