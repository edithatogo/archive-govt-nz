# Conductor Learning Log

This log is the repository-local source of truth for repeatable learning artifacts.

## 2026-06-23 — Track 18 rollout (self-learning loop implementation)
- `entry_id`: `track-18-root-legal-nz`
- `observed_on`: 2026-06-23
- `repo`: `legal-nz`
- `scope`: `track`
- `trigger`: `Track 18 implementation requires shared loop artifacts and repository-local learning surfaces`
- `severity`: `low`
- `status`: `resolved`
- `lessons_learned`:
  - Self-learning improvements need a machine-readable schema before CI automation can reason about logs.
  - Track templates without `lessons_learned` / `next_check_to_add` fields are difficult to promote safely.
  - Multiple conductor repos in this workspace need mirrored learning surfaces to avoid hidden gaps.
- `next_check_to_add`:
  - Add CI validation that checks the schema for every `learning-log.md` entry.
  - Add a lightweight step to emit learning candidates from failing workflows into `improvement-backlog.md`.
- `evidence`:
  - `conductor/templates/self-improvement-loop.md`
  - `conductor/templates/learning-entry.schema.json`
  - `conductor/templates/track-improvement-template.md`
  - `conductor/learning-log.md`
  - `conductor/improvement-backlog.md`
