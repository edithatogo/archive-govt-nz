Formal cutover release for the corpus-legislation-nz consolidation programme (epic #131).

Evidence:
- 2 successful target observation cycles (2026-08-23), each: bounded harvest -> reconciliation (consistent) -> recovery drill (verified):
  - Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32626113799
  - Cycle 2 (with full-state continuation): harvest 32625990438, reconciliation 32626071396, recovery 32626113799
- Donor repository edithatogo/corpus-legislation-nz archived 2026-08-23T07:40:08Z after the contract postcondition (2 observation cycles) was satisfied
- Attestation: evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json
- Gate authorization: evidence/migrations/corpus-legislation-nz/operational-gate-authorization.json

Supersedes invalidated receipts (observation-receipt, cutover-receipt from PR #124 era).

## Correction addendum — 2026-09-02

The Cycle 1 recovery run ID in the original release note was incorrect. The verified Cycle 1 tuple is:

- Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32625612739

Cycle 2 remains unchanged: `Cycle 2 (with full-state continuation): harvest 32625990438, reconciliation 32626071396, recovery 32626113799`. This addendum changes no tag, release asset, archived donor state, or external publication. The authoritative source is `evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json`.
