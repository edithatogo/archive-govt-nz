# Evidence

Implementation slice complete at commit `f780481`. The mapping is derived only
from archived receipt inputs, binds source and capture identities to SHA-256
content, and fails closed on stale revisions, digest/object-id drift, malformed
identities, partial/negative attempts and unresolved rights. Focused tests,
Ruff, schema validation and diff checks passed.

External reproduction, elapsed soak, production recovery, national-scale
measurement and release-authority gates remain pending.
