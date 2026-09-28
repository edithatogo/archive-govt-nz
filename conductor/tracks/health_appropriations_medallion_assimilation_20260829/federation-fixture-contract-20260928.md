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
fixity, blank or unversioned source keys, and impossible month/day shapes. The
semantic period validator also rejects impossible calendar dates, mixed
precision bounds, and reversed intervals. No federation table or partner link
is produced.

## Verification

- Federation contract tests: 18 passed, including live-runtime, unproven map,
  unsupported confidence, missing lineage fixity, missing/blank source keys,
  invalid calendar intervals, invalid tokens/year zero, and unversioned-key
  rejection. The semantic period validator has 100% statement and branch
  coverage.
- Schema registry: 52 schemas and 42 representative documents validated.
- Ruff and basedpyright passed for changed Python files.
- PR review corrections tightened source-key nullability and added strict
  calendar/order checks for periods. The corrected full `./scripts/validate.sh`
  completed successfully after the additional invalid-token coverage.

Approved links to `reimbursement-atlas` and `global-medicines-atlas` remain
pending source-level mapping evidence and human review. These fixtures do not
claim semantic equivalence or partner availability.
