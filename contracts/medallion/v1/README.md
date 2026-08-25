# Medallion conformance vocabulary v1

This directory is a byte-versioned interoperability contract shared by
`reimbursement-atlas`, `global-medicines-atlas`, and `archive-govt-nz`.
Each repository validates its own projections locally; no shared runtime package
or cross-repository checkout is required.

The vocabulary standardizes layer names, SHA-256 identity, explicit lineage,
rights decisions, promotion states, and fail-closed promotion semantics. An
`approved` decision is conformant only when the transition is adjacent, every
required gate is present in `passed_gate_ids`, rights are `approved`, input
checksums match the subject lineage, and `fail_closed` is `true`.

Changes require a new version directory. Existing versions are immutable.
