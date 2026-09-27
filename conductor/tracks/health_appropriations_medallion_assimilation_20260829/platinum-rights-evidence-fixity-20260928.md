# Platinum per-resource rights evidence fixity

The local metadata-application validator now accepts a separately supplied
mapping of rights-evidence SHA256 pins to exact bytes. Every
`eligible_asserted` resource must have matching supplied bytes. Missing,
altered, malformed, and unreferenced evidence fails closed. Unresolved and
restricted resources continue to require null licence and evidence claims.

The receipt records the count of evidence payloads whose bytes were verified.
This proves only byte fixity against the supplied assertion. It does not verify
the source or authority of an assertion, determine legal rights, grant release
readiness, or authorize publication.

## Verification

- Focused metadata-application tests: 118 passed, including missing, altered,
  and unreferenced evidence, mixed per-resource rights states, and retained
  publication denial.
- `./scripts/validate.sh`: passed with 7,012 tests, 9 skipped, 98.15% branch
  coverage, 49 schemas and 39 representative documents, parity 9/9, all
  mutation gates, and dependency/licence/secret/SBOM checks.
- Hosted pull request checks: pending.
