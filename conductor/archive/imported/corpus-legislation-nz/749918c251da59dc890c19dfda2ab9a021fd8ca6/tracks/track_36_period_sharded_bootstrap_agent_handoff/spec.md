# Spec - Period-Sharded Bootstrap Agent Handoff

## Status
ready

## Goal
Make the corpus explicitly divisible into time-period shards so completed
periods can be handed to other agents for review, triage, upload preparation,
documentation, or downstream tasks while later periods continue to sync.

## Scope

- Define canonical period shards from the reviewed seed inventory.
- Use coarse historical shards where legislation density is lower and annual
  shards for recent/API-native coverage where yearly change volume and
  operational reuse are higher.
- Generate period-specific seed files and a machine-readable period manifest.
- Emit per-period workflow checkpoint artifacts as soon as a period completes.
- Add review and handoff evidence so another agent can safely pick up a
  finished period without waiting for the entire full-corpus run.

## Proposed Period Policy

Period boundaries must be generated from source metadata, not inferred from
filename ordering alone. The initial policy is:

- `pre_1908`: all works before 1908.
- `1908_1949`: 1908 through 1949.
- `1950_1979`: 1950 through 1979.
- `1980_1999`: 1980 through 1999.
- `2000_api_boundary_minus_1`: 2000 through the year before the verified
  API-native/recent boundary.
- Annual shards from the verified API-native/recent boundary through the
  current year, for example `year_2020`, `year_2021`, and so on.

The API-native/recent boundary is deliberately an implementation task. Do not
hard-code it from memory. Verify it against project evidence, official API
metadata, or generated coverage evidence before promoting the final boundary.
If no authoritative boundary is available, use a conservative fallback boundary
of 2008 for planning only and record the uncertainty in the manifest.

## Acceptance Criteria

- A period policy document or manifest describes every shard, its year range,
  source rule, work-ID count, SHA-256, and status.
- `seeds/periods/` or equivalent generated artifacts contain one seed file per
  period.
- Each work ID belongs to exactly one period shard.
- The period manifest records any work IDs whose year cannot be derived and
  routes them to an explicit review shard, not silently into a period.
- The full-corpus workflow can produce a checkpoint artifact after each period
  completes, including records, validation, manifest, coverage, sync state, and
  period metadata.
- The review gate can review a single completed period artifact and report
  failed versions, missing text, missing XML URLs, ephemeral IDs, record counts,
  and manifest hash.
- Conductor records which periods are ready for agent handoff, in review,
  blocked, or completed.
- Public completeness claims remain blocked until all periods are reviewed and
  reconciled.

## Evidence to Record

- API-native/recent boundary decision, source, verification status, and warning
  when the boundary is only a planning fallback.
- Period manifest path and SHA-256.
- Per-period seed file paths and SHA-256 values.
- Per-period workflow artifact names and run URLs.
- Per-period validation, manifest, coverage, and sync-state summaries.
- Agent handoff owner/status for each period.
- Any unknown-year or ambiguous-year work-ID triage list.

## Evidence Recorded

- `nzlc split-work-id-periods` now generates period seed files and a period
  manifest.
- `.github/workflows/full_corpus_period_bootstrap.yml` runs a single period,
  writes `generated/full-corpus-periods/period_context.json`, validates,
  manifests, builds coverage, runs the review gate, and uploads a period
  checkpoint artifact.
- `nzlc review-full-corpus-bootstrap` includes period context when a period
  checkpoint artifact provides it.
- The API-native/recent boundary remains unverified by default. The CLI records
  `api_boundary_source`, `api_boundary_verified`, and
  `api_boundary_decision`; the default source is
  `planning_fallback_unverified` with boundary year `2008` and a manifest
  warning that blocks API-native boundary claims until authoritative evidence is
  supplied.

## Dependencies

- Track 04 source discovery inventory and year derivation evidence.
- Track 07 full-corpus bootstrap workflow and artifact review gate.
- Track 17 runtime batching and resume rules.
- Track 18 data-quality and schema governance.
