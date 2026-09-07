# Chart packaging integration

First full gate at `acf06c153c1f6900262da588c0308a57bb5dd985`:
6,490 tests passed, combined coverage 98.0436%, schema/parity/mutation/hygiene
gates passed, CAS 706.31 MB/s, dependency audit and licence inventory passed.
The process exited 1 at secret scanning: one new entropy candidate was the
generated local macOS temporary-directory path in the HYEFU replay receipt.
It was inspected as a non-secret output location. SBOM did not run in this attempt.

The existing replay was run again into a fresh simpler `/tmp` path, producing
identical verified outputs. Its location-only receipt refresh and original path
are documented in `hyefu16-package-20260907/evidence.md`. Scanner controls are
unchanged. The corrected combined full gate remains pending.

Independent review also found an integration-only P2 in the expanded coverage
recipe: new chart inventory fields changed reproduction of historical pinned
receipt bytes. That finding remains open until an explicit historical receipt
contract is implemented and independently re-reviewed; pins must not be silently
replaced. The 16, 86 and six chart package slices separately cleared independent
source replay and regression review, without semantic or rights promotion.
