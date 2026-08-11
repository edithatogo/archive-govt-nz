# Evidence index

The deterministic synthetic fixture corpus is present under `fixtures/` with a
manifest, metadata JSON, payload text, and README. The manifest records SHA-256
digests for the metadata and payload files. The focused validator and evaluation
tests passed 4/4 on 2026-08-11.

This verifies fixture hash closure only. No RO-Crate, BagIt, or OCFL conformance
claim has been made, and no release requirement has been adopted. Results remain
distinct from independent validator evidence.

The bounded BagIt fixture contains the same metadata and payload bytes under
`data/`, with a SHA-256 payload manifest and UTF-8 BagIt tag file. The focused
closure tests pass; this is transfer-package evidence only, not a release
authorization or full BagIt conformance claim.

The bounded OCFL fixture contains an inventory with a `v1` head, linked version
state, and a non-empty `v1/content` directory. The validator requires those
links and does not claim full OCFL conformance or production storage adoption.

No local reference executables for BagIt, RO-Crate, or OCFL were available on
2026-08-11. This is recorded as `unavailable`, not `verified`; the structural
fixture validators remain bounded self-checks and do not substitute for
independent conformance validation.
