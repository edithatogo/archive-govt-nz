# Track 10 Specification: Canary Migration and Dual Operation

## Purpose
Validate staged end-to-end migration in live shadow mode on one low-risk public source family (e.g. ministerial RSS feeds or a public Bluesky account) before broader adapter cutover.

## Context & Objectives
1. Run donor and target concurrently on the selected canary source family.
2. Verify live network behavior, rate-limiting, and error recovery in shadow mode without publishing to production channels.
3. Conduct a live rollback rehearsal.
4. Execute publication dry-runs to verify Hugging Face and Zenodo payload parity.

## Deliverables
- `evidence/migrations/sm-govt-nz/canary-run-report.json`
- Dual-run operational receipt
