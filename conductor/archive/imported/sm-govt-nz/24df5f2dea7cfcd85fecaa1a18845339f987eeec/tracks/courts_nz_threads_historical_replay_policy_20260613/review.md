# Review - Courts of New Zealand Threads Historical Replay Policy

**Track ID:** `courts_nz_threads_historical_replay_policy_20260613`
**Review Date:** 2026-06-25
**Reviewer:** Conductor Track Reviewer Agent

## Summary
All 10 tasks across 3 phases are fully implemented. The track delivers a written policy decision that Threads historical replay is deferred and must remain disabled. No fixes required.

## Plan Compliance

| Phase | Task | Status | Evidence |
|-------|------|--------|----------|
| Phase 1: Platform Constraints | Confirm current Threads API posting limits and unsupported backdating behavior | âœ… | Documentation reviewed; Threads API cannot backdate |
| Phase 1: Platform Constraints | Estimate replay duration and daily volume for 738 archive records | âœ… | Capacity estimate documented in plan |
| Phase 1: Platform Constraints | Identify whether media or link handling changes replay risk | âœ… | Risk analysis completed |
| Phase 2: User-Facing Risk Review | Assess how archival posts would appear in a current Threads feed | âœ… | Feed-noise analysis documented |
| Phase 2: User-Facing Risk Review | Compare alternatives: profile link, pinned explainer, sampled replay, or no replay | âœ… | Alternatives evaluated |
| Phase 2: User-Facing Risk Review | Define account trust and moderation guardrails | âœ… | Guardrails defined |
| Phase 3: Decision | Write the recommended replay policy | âœ… | `conductor/threads_historical_replay_status_20260614.json` |
| Phase 3: Decision | Update Threads adapter launch requirements based on the decision | âœ… | Adapter updated |
| Phase 3: Decision | Create a follow-up implementation track only if replay is approved | âœ… | No follow-up needed (replay rejected) |
| Phase 3: Decision | Keep `archive_replay_enabled` false for Threads and test that enabling it blocks the posting command | âœ… | `tests/test_post_threads_latest.py::test_historical_replay_flag_blocks_threads_posting` |

## Spec Compliance
- âœ… Threads historical replay treated as current publication of archival records
- âœ… Original source timestamps preserved in post text and corpus metadata
- âœ… Estimate of user-facing noise, API quota impact, account trust risk, and moderation risk completed
- âœ… Approval criteria defined before any historical Threads replay job is built
- âœ… `archive_replay_enabled` remains false for Threads

## Acceptance Criteria
- âœ… Written decision recommends `deferred_do_not_replay`
- âœ… Decision cites platform limits, account-risk considerations, and corpus preservation alternatives
- âœ… No implementation track needed (replay rejected)
- âœ… Corpus remains available through GitHub Pages, Hugging Face, Zenodo, and Bluesky mirror replay

## Decision
**Deferred - Do Not Replay.** Threads cannot backdate historical posts. Archive replay would appear as current publication and create user-facing feed noise. Live/ongoing Threads posting continues, but archive records are not replayed to Threads. Historical access is handled through the repository corpus, GitHub Pages, Hugging Face, Zenodo, and Bluesky mirror replay.

## Code Quality
- Ruff: âœ… All checks passed
- pytest: âœ… All 439 tests passed

## Archive Decision
**ARCHIVED** â€” All deliverables complete and verified.

## Review Evidence
- `conductor/tracks/courts_nz_threads_historical_replay_policy_20260613/plan.md` â€” All 10 tasks marked [x]
- `conductor/tracks/courts_nz_threads_historical_replay_policy_20260613/spec.md` â€” Spec fully implemented
- `conductor/threads_historical_replay_status_20260614.json` â€” Decision recorded: `deferred_do_not_replay`
