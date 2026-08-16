# Plan

- [x] Implement serial four-per-day backfill and account audit state.
- [x] Add historical attribution and public-readback requirements.
- [x] Repair the Courts canary and complete its backfill.
- [ ] Select and observe two smallest-backlog pilots.
- [ ] Continue sequential rollout until all eligible identities are live, complete, or evidence-backed terminal.

## Pilot selection snapshot (2026-07-27)

- ACC is the first live pilot; cleanup is verified complete and post-remediation observation remains open through 2026-08-03.
- `conductor/bluesky_mirror_pilot_candidates.json` applies
  `eligible_backlog_ascending_then_mirror_id` to the fail-closed source contract.
- Electoral Commission (`#85`) is the next operator-supervised pilot with one
  eligible unique record. Account registration, profile configuration,
  credentials, preflight, and posting remain separate operator gates.
