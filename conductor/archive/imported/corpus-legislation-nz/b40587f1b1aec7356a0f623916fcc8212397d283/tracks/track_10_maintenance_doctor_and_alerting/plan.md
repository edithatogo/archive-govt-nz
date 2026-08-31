# Plan - Maintenance Doctor And Alerting

## Tasks
- [x] Confirm `.github/workflows/doctor.yml` exists.
- [x] Confirm local non-network doctor runs without mutating corpus data.
- [x] Review Dependabot configuration and security workflows.
- [x] Use GitHub Actions default notifications initially.
- [x] Document notification path and operator routine:
      GitHub Actions default email notifications to repo watchers on failure.
      `docs/maintenance_runbook.md` documents the weekly check routine.
- [x] Doctor workflow passed with live secrets:
      Run `27125139848` (2026-06-08) and run `27362180628` (2026-06-11) both
      succeeded.
