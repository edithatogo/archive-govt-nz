# Requirements: Conductor Claim Drift Detection

## Background
Conductor records can drift from GitHub reality unnoticed: the sm-govt-nz
closeout receipt claimed archival while the repo remained active. A scheduled,
machine-checkable comparison closes this class of integrity error.

## Core requirements
1. For every external repository referenced by conductor records, query GitHub API state: archived flag, open issues/PRs, recent workflow activity.
2. Compare against recorded claims (receipts, registry dispositions) and fail closed on divergence with bounded evidence.
3. Run weekly on a schedule lane; never mutate state — detection only.
4. No credentials beyond existing token scopes; no write operations.
