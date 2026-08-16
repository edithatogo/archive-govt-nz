# Plan - NZ Government Discovery - self-improving heuristic search and learning loop

## Dependencies
Depends on `govt_archive_readiness_matrix_20260625`.

## Phase 1: Heuristic Corpus
- [x] Task 1: Track successful and failed discovery hedges for government domains and public-sector entity classes.
- [x] Task 2: Persist evidence snippets, referring pages, query strings, and candidate scores.
- [x] Task 3: Classify official, role/office, personal-public, campaign, legacy, duplicate, and spoof-risk accounts.

## Phase 2: Daily Discovery
- [x] Task 4: Run daily GitHub Actions discovery in bounded dry-run mode.
- [x] Task 5: Probe homepages, contact pages, footers, sitemaps, RSS auto-discovery, and YouTube links.
- [x] Task 6: Emit candidate reports with new/already-registered/rejected/needs-review buckets.

## Phase 3: Learning Loop
- [x] Task 7: Promote high-yield heuristics and demote noisy ones.
- [x] Task 8: Store false-positive patterns.
- [x] Task 9: Use deterministic scoring before any LLM summarization.

## Phase 4: Review and Handoff
- [x] Task 10: Run `$conductor-review` before bulk imports.
- [x] Task 11: Auto-apply provenance/schema fixes.
- [x] Task 12: Add git notes with heuristic changes and candidate-count deltas.

