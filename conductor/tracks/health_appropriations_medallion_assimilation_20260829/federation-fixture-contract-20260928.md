# Health federation fixture contract

This offline contract records the provenance fields required before a Health
record can be compared with a partner namespace: namespace, scheme version,
key, mapping method, confidence, period basis, pinned manifests and source/target
record identities. The committed examples are synthetic fixtures only. They
cover unmatched and ambiguous dispositions, with method `none` and confidence
`null` because no mapping evidence has been reviewed.

The schema accepts only `offline_fixture` observations and unresolved
dispositions. It rejects live-runtime claims, mapped/approved dispositions,
asserted methods or confidence without a reviewed evidence contract, invalid
fixity, and unversioned keys. No federation table or partner link is produced.

## Verification

- Federation contract tests: 7 passed, including live-runtime, unproven map,
  unsupported confidence, missing lineage fixity and unversioned-key rejection.
- Schema registry: 52 schemas and 42 representative documents validated.
- Ruff and basedpyright passed for changed Python files.

Approved links to `reimbursement-atlas` and `global-medicines-atlas` remain
pending source-level mapping evidence and human review. These fixtures do not
claim semantic equivalence or partner availability.
