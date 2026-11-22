# Election publication integrity and solo-developer assurance (2026-11-11)

## Problem
The public static Space was displaying synthetic or unverified 2026 numerical claims as preliminary electoral results. The retained repository fixture has not yet been qualified against an authoritative source capture. The archive release view must distinguish a reproducible repository record from independently established election facts. Existing research assets and history remain retained; future analytical work follows the downstream handoff boundary in `docs/roadmap.md`.

## Must (P0)
- [x] Retain the fixture with its recorded 7 November 2026 preliminary vintage unchanged as an unverified repository reference; authoritative source validation remains pending.
- [x] Implement a fixture-driven archival landing page with runtime type/arithmetic validation, accessible status, explicit unverified/provisional labels, and clear separation from retained research. Hosted and deployed qualification remain open below.
- [x] Add CI publication integrity regression and fail deployment if Hugging Face credentials are missing.
- [x] Fix excluded-party handling for Gallagher and Loosemore–Hanby metrics.
- [ ] Run all focused election unit tests and full repository quality/security checks on exact PR head; repair any failures before merge.
- [ ] Merge only once checks pass and verify the served Space revision/data after main deployment.

## Should (P1)
- [ ] Snapshot official Commission content with provenance hashes and parse the immutable source instead of manually transcribing a reference.
- [ ] Confirm legal statutory tie handling and add property/metamorphic allocation tests.
- [ ] Recompute the 2026 election Gold derivatives from official preliminary observations and invalidate stale outputs.
- [ ] Inventory retained graphs, forecasts, MMP models and causal claims for downstream handoff; keep the archive release view limited to qualified source access.
- [ ] Add browser/mobile/accessibility smoke tests and exact release manifests; pin toolchain/actions/lockfiles.
- [ ] Resolve existing security/privacy scanning PR #860 with exact-head CI and independent assessment.

## Could (P2)
Research expansion is retained here as historical backlog for downstream consuming applications, not new analytical scope for the archive release view.
- [ ] Restore interactive special-vote and coalition scenarios with distributions, assumptions and uncertainty.
- [ ] Add signed source-to-deployment artifact attestations, reproducible builds and rollback testing.
- [ ] Build longitudinal benchmark comparisons and research appendices only after empirical validation.

## Evidence and limitations
The fixture records these source references; neither was independently captured or validated in this repair:
- https://elections.nz/media-and-news/2026/2026-general-election-preliminary-results
- https://www.electionresults.govt.nz/electionresults_2026_preliminary/

The historical 2023 'official' capture receipt is not a 2026 official release. The fixture records 27 November as its expected declaration date; that metadata is not independent confirmation. Nothing in this track claims that a PR has passed hosted CI or deployed to HF until independently verified.

### Archival release-view repair receipt (2026-11-22)
- Baseline PR head `9fb6b7c46fd32e5f4f0c54355b79568ca64bd5f8` failed the existing publication regression because the retained landing page never loaded `data/2026-preliminary.json`. That page and its failing assertions were unchanged from main; the earlier checked UI item lacked an implementation matching its contract.
- The replacement loads only the local JSON fixture and renders its recorded metadata and party rows through text nodes. It checks supported identity, dates, numeric types/ranges, unique party names, row and aggregate seat arithmetic, party-vote sums, majority and safe source-link hosts. Missing, malformed or inconsistent data clears the values and exposes an accessible error status. The unverified notice remains visible after successful internal checks.
- The fixture is unchanged: SHA-256 `6f3d511f82b78e2f06fa4147db893cf24d9af638cf1ec84c26c2e2ec71055251`. Existing fixture/statistical assertions are preserved. Research assets, source history and the deployment script are unchanged; no source capture, dependency/CDN, forecast or causal method is added.
- Focused command: `./scripts/test-focused.sh tests/test_elections_publication_integrity.py tests/tools/test_workflow_policy.py -q` — **63 passed** (53 publication tests and 10 workflow-policy tests), using the pinned local Python 3.15.2 and existing Node runtime. New tests execute the exact inline module with offline responses, including invalid identities, dates, types, totals, duplicate parties, integer overflow, unsafe links, missing responses and malformed JSON.
- Affected Ruff lint and format checks passed. Scoped `basedpyright tests/test_elections_publication_integrity.py --threads 1` reported **0 errors, 0 warnings**. The workflow-policy change removes only the import-block blank line identified by Ruff in all three hosted assurance jobs.
- An offline Chromium/Playwright smoke run was attempted with every request intercepted, but Chromium failed before page execution because this executor denied a required socket (`Operation not permitted`). Browser/mobile/keyboard behavior and deployed parity remain **unverified**; no successful browser receipt is claimed. No dependencies were installed to work around this limit.
- The complete hosted checks must qualify the follow-up commit, including the configured four-worker type stage that the previous head never reached. Source-capture validation, the full assurance gate and served Space revision/data checks remain open. No remote write or deployment was performed during this local repair.
