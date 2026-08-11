# Evidence

## Final resource-level gate

- Official CKAN-derived resource metadata: 158 resources across 28 Ministry of
  Health datasets.
- Eligible resource receipts: 0.
- Rights-restricted/decision-required tombstones: 158.
- Payload attempts: 0.
- Captured originals: 0.
- Publication: not authorized and not attempted.

The enabled capture runner consumed the generated resource-level plan and
recorded `attempted: 0` and `payload_transfer: false`. Secure preflight evidence
is now an additional gate for already-eligible resources and cannot promote a
restricted resource.

## Prepared package

`evidence/prepared-package/` contains unchanged source evidence, normalized
JSONL and Parquet metadata, explicit tombstones, the capture plan and run
receipt, a human-readable summary, and a checksum manifest using SHA-256 and
BLAKE3. Its state is `prepared-not-published`.

No WARC was created because no source transaction was eligible. No payload was
quarantined because no payload was transferred. These are explicit
not-applicable outcomes, not completeness claims.

## Assurance

- Resource-rights contract: secure availability cannot override restriction.
- Property test: selected resources are always policy-eligible.
- Metamorphic test: input order cannot alter the selected identifier set.
- Deterministic simulation: repeated package preparation produces identical
  manifest, JSONL, Parquet, and tombstone bytes.
- Mutation gate: rights-disposition and preflight-confirmation mutants are
  required to be killed by the repository harness.
- Critical package logic: 14 focused tests, 100% line and branch coverage.
- Repository harness checkpoint: 373 tests passed with 96.48% overall coverage;
  schemas, all mutation lanes, dependency audit, licences, secret scan, and
  CycloneDX SBOM validation passed.
- GitHub tracking: #76; nested phases #77-#80.
