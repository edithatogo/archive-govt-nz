# Evidence

Implementation slice complete at commit `f780481`. The mapping is derived only
from archived receipt inputs, binds source and capture identities to SHA-256
content, and fails closed on stale revisions, digest/object-id drift, malformed
identities, partial/negative attempts and unresolved rights. Focused tests,
Ruff, schema validation and diff checks passed. Commit `d17873d` also rejects
malformed object IDs, source URLs and timestamps. The full repository harness
then passed on Python 3.14.5: 1,516 tests, 95.94% coverage, schema validation,
parity, mutation, security, dependency, secret and SBOM checks.

External reproduction, elapsed soak, production recovery, national-scale
measurement and release-authority gates remain pending.
