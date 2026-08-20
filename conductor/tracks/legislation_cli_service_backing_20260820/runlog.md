# Run log

- 2026-08-20T11:12:00Z: Created local branch
  `codex/legislation-cli-correction` at global CLI head `2c86d90`. Audit found
  duplicated sync transport with a fabricated default work and fixed timestamp,
  flat-CAS counting, record-count denominators, absent change state reported as
  observed, manifest-only publication reported staged, and token-only remote
  publication reported verified. No push, PR, merge, or live action occurred.
- 2026-08-20T11:17:00Z: Added seven adversarial contract tests. The red run
  failed all seven against the merged CLI: absent changes returned success;
  coverage used manifested records as its own denominator; a flat garbage CAS
  returned operational; unknown `nzlc` input silently invoked status; empty
  sync constructed state and returned success; a corrupt manifest root
  validated; and manifest/token publication evidence returned affirmative
  states. This is the expected red baseline.
- 2026-08-20T11:28:00Z: Routed sync through `LegislationArchiveService`, made
  selection and batch identity explicit, authenticated manifest roots and
  discovered-inventory coverage, required linked manifest/checkpoint/sharded
  CAS state for operational status, removed token-only verification, and made
  absent change evidence and unknown compatibility actions non-zero. Focused
  CLI suite passed 32 tests with Ruff and BasedPyright green. Replay linkage,
  expanded adversarial coverage, full harness, and review remain pending.
