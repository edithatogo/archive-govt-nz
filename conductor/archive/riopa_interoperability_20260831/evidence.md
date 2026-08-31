# Evidence

Implementation slice complete at commit `f780481`. The mapping is derived only
from archived receipt inputs, binds source and capture identities to SHA-256
content, and fails closed on stale revisions, digest/object-id drift, malformed
identities, partial/negative attempts and unresolved rights. Focused tests,
Ruff, schema validation and diff checks passed. Commit `d17873d` also rejects
malformed object IDs, source URLs and timestamps. The full repository harness
then passed on Python 3.14.5: 1,516 tests, 95.94% coverage, schema validation,
parity, mutation, security, dependency, secret and SBOM checks.

The Codecov patch gap was closed at commit `969e7f5`; the focused mapping
suite now covers 100% of statements and branches (15 tests).

External reproduction, elapsed soak, production recovery, national-scale
measurement and release-authority gates remain pending.

## Closeout correction

Unknown/withdrawn capture and uncertain legal states now remain quarantined.
New exports explicitly disable seven operational/authoritative claims while
preserving original observations. Agent-panel review passed after a malformed
legal-state correction. See `closeout-correction-validation.json` for bounded
validation evidence: local full assurance failed under resource pressure and
hosted assurance is pending. Earlier PR #260 success does not qualify this fix.
The track remains in progress and has not been archived.

## Final hosted qualification, 2026-08-31

The prior subsection records the pre-CI state and is superseded by
`hosted-closeout.json`. All seven checks passed on corrected head `174b766`,
including the full Python 3.14 Assurance harness on Ubuntu, macOS and Windows.
PR #279 merged as `1b2d7c0699c0629875657ba04cf0c989aaad00c2`.
This completes bounded acceptance and permits this track's archive. Historical
local failures remain unchanged and do not represent a local full-harness pass.

Acceptance mapping: schema-valid deterministic identities and pinned replay are
tested in `tests/riopa/test_receipt_mapping.py`; digest/revision mismatch and
malformed identities reject; partial/negative and unknown/legal states quarantine;
schema validation rejects enabled claims. All seven claim flags remain false.
Agent-panel review is recorded in `review.md`; hosted qualification is separately
recorded above. No live source, publication, external participant, elapsed soak,
production recovery, national measurement or release approval is inferred.
