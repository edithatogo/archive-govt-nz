# Platinum per-resource rights evidence fixity

The local metadata-application validator now accepts a separately supplied
mapping of rights-evidence SHA256 pins to exact bytes. Every
`eligible_asserted` resource must have matching supplied bytes. Missing,
altered, oversized, malformed, and unreferenced evidence fails closed. Each
evidence item is capped by the existing per-payload limit, and all supplied
evidence shares the existing aggregate byte limit. Unresolved and restricted
resources continue to require null licence and evidence claims.

The receipt records the count of evidence payloads whose bytes were verified.
This proves only byte fixity against the supplied assertion. It does not verify
the source or authority of an assertion, determine legal rights, grant release
readiness, or authorize publication.

## Verification

- Focused metadata-application tests: 118 passed, including missing, altered,
- Focused metadata-application tests: 119 passed, including missing, altered,
  oversized, aggregate-limit, and unreferenced evidence, mixed per-resource
  rights states, and retained publication denial.
- `./scripts/validate.sh` before the bounded-evidence review fix: passed with
  7,012 tests, 9 skipped, 98.15% branch
  coverage, 49 schemas and 39 representative documents, parity 9/9, all
  mutation gates, and dependency/licence/secret/SBOM checks.
- `./scripts/validate.sh` after the bounded-evidence review fix: passed with
  7,013 tests, 9 skipped, 98.15% branch coverage, 49 schemas and 39
  representative documents, parity 9/9, all mutation gates, and
  dependency/licence/secret/SBOM checks.
- Exact-head hosted checks after this review fix: pending.
