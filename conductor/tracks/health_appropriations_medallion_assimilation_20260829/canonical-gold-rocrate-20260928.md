# Canonical Gold RO-Crate inventory

Canonical Gold builds now include a deterministic `ro-crate-metadata.json`
that inventories the actual Parquet and PNG payload bytes. The crate graph binds
each file's basename, media type, byte count and SHA-256; the enclosing Gold
manifest separately binds the crate file itself. The crate does not list itself
as a payload.

This is a local technical inventory. It has no license, publisher, publication
date, access URL or rights approval. The Gold manifest continues to report
`rights_state: not_evaluated` and `publication: not_performed`. This slice does
not validate application-level semantics, call a standards processor, or
complete the remaining Platinum products.

## Verification

- Regression checks independently read every emitted table, plot and crate
  file, compare file size and SHA-256 with the RO-Crate nodes, confirm exact
  `hasPart` inventory and deterministic repeat-build bytes, and assert absent
  license/publication fields.
- Focused canonical Gold checks: 16 passed with 100% statement and branch
  coverage. The repeated build was byte-identical, and the read-only canonical
  verifier accepted the emitted crate as part of the exact output inventory.
- Full `./scripts/validate.sh` passed: 7,073 tests passed, 9 skipped, 98.18%
  branch coverage; 52 schemas/42 representative documents, parity 9/9,
  mutation, hygiene, benchmark, dependency, license, secret and SBOM checks all
  passed.
- Hosted pull-request checks are recorded after delivery.
