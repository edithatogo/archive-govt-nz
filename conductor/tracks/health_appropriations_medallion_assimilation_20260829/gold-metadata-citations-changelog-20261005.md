# Gold metadata citations and snapshot changelog

This slice adds deterministic `citations.json` and `changelog.json` projections
to the existing pinned Fiscal analytical and Budget comparison Gold metadata
build. Both are rebuilt from the exact verified package manifests and bind each
record to its content-addressed package identifier and manifest SHA256.

The citation projection identifies only local Gold snapshots;
`source_citation` remains `not_asserted`. The changelog is a current snapshot
inventory and does not compare against a prior release or claim that rows are
new or changed. Rights and publication states are copied from the verified Gold
manifests, which this producer currently accepts only as `not_evaluated` and
`not_performed`. No federation links are emitted: reviewed source-level mapping
evidence and approval are not present. No licensing, external URL, or source
redistribution claim is added.

Both projections have closed JSON Schemas with representative fixtures and are
validated against the generated payloads during the focused metadata tests.

Focused validation: `uv run pytest
tests/domains/health_appropriations/test_gold_metadata.py -q` passed (3 tests),
including reversed-input deterministic replay, manifest-bound citation and
changelog assertions, tamper rejection, and offline DCAT/PROV graph checks.
The full repository validation harness and hosted PR checks remain required
before merge.
