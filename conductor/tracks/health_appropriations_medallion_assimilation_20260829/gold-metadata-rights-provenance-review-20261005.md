# Gold metadata rights provenance review

## Scope

This review covers the two local Gold packages currently admitted to the
Platinum metadata projection: Fiscal analytical Gold and Budget comparison
Gold. It checks the exact pinned package manifests and the generated
catalogue, citation, changelog, and source-drill-through records. It is not a
rights determination for the underlying source resources and does not approve
distribution or publication.

## Source records and generated statements

| Package | Manifest SHA-256 | Manifest rights | Manifest publication | Generated catalogue, citation, changelog |
|---|---|---|---|---|
| Fiscal analytical | `1b79d6f582dc8e9935e16bce2d3fe78b78d77e2a68aacf201ac9118b28462fa2` | `not_evaluated` | `not_performed` | `not_evaluated`, `not_performed` |
| Budget comparison | `e8c7efda7773368bcee1b7f596f373c0aa6ec3f4453485b9b6fb9cc447ebd5fc` | `not_evaluated` | `not_performed` | `not_evaluated`, `not_performed` |

The pinned bytes were read from the retained Gold manifests. Neither manifest
contains a licence/licensing field. The four projections identify the same
manifest pins and preserve the two states above; they add no licence assertion.
The source-drill-through projection carries the same package pins and preserves
`not_evaluated` / `not_performed`; it makes no affirmative rights or publication
assertion. This verifies provenance and faithful propagation of the recorded
metadata states, not the legal correctness of those states.

The reproducible projection evidence is retained at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/assurance/gold-metadata-20261005-v2/first`
and its byte-identical repeat build at
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/assurance/gold-metadata-20261005-v2/second`.
The code enforces
`not_evaluated` and `not_performed` against each pinned manifest before it
emits the projections. Existing schema and tamper tests cover those contracts.

## Disposition

- The Gold metadata statements are supported as faithful copies of their exact
  package-manifest fields; no blanket or inferred licence was emitted.
- Resource-level rights eligibility, redistribution rights, and publication
  remain unresolved. Do not upgrade these states without resource-specific
  evidence and the required review.
- Approved links to `reimbursement-atlas` and
  `global-medicines-atlas` remain absent. Current federation fixtures establish
  rejection behavior for unmatched, ambiguous, and unproven mappings, but no
  approved mapping evidence was found for either partner. This is an evidence
  and approval gap, not a schema defect; continue to emit no federation rows.
- This bounded review does not close the broader Phase 7 rights review, which
  must cover other metadata surfaces and resource-level evidence.

## Verification

- Recomputed SHA-256 for both source package manifests and matched the package
  pins in the generated catalogue, citations, and changelog.
- Compared rights and publication values in all three projections with their
  pinned source manifest records; confirmed no licence field in either source
  manifest or the generated projections.
- Confirmed the source-drill-through rows are pinned to the same two manifests
  and preserve the unassessed rights/publication states.
- Existing focused metadata tests and `./scripts/validate.sh` validate the
  projection schemas, rights-state propagation, altered-input rejection, and
  deterministic rebuild contract.
- `./scripts/validate.sh` on this review passed: 7,489 tests passed, 10 skipped;
  97.77% coverage against the 80% floor; 56 schemas and 46 representative
  documents; parity 9/9; all configured mutation, hygiene, benchmark,
  dependency, licence, secret, and SBOM checks passed.
