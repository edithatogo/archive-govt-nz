# Election publication integrity and solo-developer assurance (2026-11-11)

## Problem
The public static Space was displaying synthetic or unverified 2026 numerical claims as preliminary electoral results. The source GitHub repo already has election engines, schemas, workflows and research tracks, but did not consistently gate publication against Electoral Commission figures.

## Must (P0)
- [x] Freeze Electoral Commission 7 November 2026 preliminary party-vote/seat fixture.
- [x] Replace the public landing page with source-vintage-driven results, runtime arithmetic validation, accessibility labels, explicit provisional status, and clear separation from experimental research.
- [x] Add CI publication integrity regression and fail deployment if Hugging Face credentials are missing.
- [x] Fix excluded-party handling for Gallagher and Loosemore–Hanby metrics.
- [ ] Run all focused election unit tests and full repository quality/security checks on exact PR head; repair any failures before merge.
- [ ] Merge only once checks pass and verify the served Space revision/data after main deployment.

## Should (P1)
- [ ] Snapshot official Commission content with provenance hashes and parse the immutable source instead of manually transcribing a reference.
- [ ] Confirm legal statutory tie handling and add property/metamorphic allocation tests.
- [ ] Recompute the 2026 election Gold derivatives from official preliminary observations and invalidate stale outputs.
- [ ] Inventory all graphs, forecasts, MMP models and causal claims, then move only validated work into results UI.
- [ ] Add browser/mobile/accessibility smoke tests and exact release manifests; pin toolchain/actions/lockfiles.
- [ ] Resolve existing security/privacy scanning PR #860 with exact-head CI and independent assessment.

## Could (P2)
- [ ] Restore interactive special-vote and coalition scenarios with distributions, assumptions and uncertainty.
- [ ] Add signed source-to-deployment artifact attestations, reproducible builds and rollback testing.
- [ ] Build longitudinal benchmark comparisons and research appendices only after empirical validation.

## Evidence and limitations
Primary Commission release: https://elections.nz/media-and-news/2026/2026-general-election-preliminary-results
Provisional results: https://www.electionresults.govt.nz/electionresults_2026_preliminary/
The historical 2023 'official' capture receipt is not a 2026 official release. The 2026 official result is expected 27 November. Nothing in this track claims that a PR has passed hosted CI or deployed to HF until independently verified.
