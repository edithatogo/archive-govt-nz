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

## Corrected combined validation

The full locked gate at `bafecb48673a64c1af5ed3395aa2fbabf1ef3253` exited 0:
6,501 tests passed, 98.0436% combined coverage, 48 schemas/38 representative
documents, 9/9 differential cases, all configured mutation/hygiene gates,
CAS throughput 618.35 MB/s, dependency audit, licence inventory, secret scan
and validated 112-component SBOM. Fifteen test warnings remain disclosed;
no scanner or coverage controls were weakened. The earlier failed gate above
remains historical evidence, not a passing run.

Independent Conductor reviews cleared all three chart packaging increments:
205 tests for HYEFU16, 154 for BEFU86 and 197 for residual6, with actual retained
source replay and unchanged earlier package hashes. These overlapping focused
counts are not added together as unique tests. The combined package represents
108 distinct raw/context observations, not additive financial amounts.

The coverage P2 was fixed in `bafecb48` using an explicit schema-checked,
hash-bound historical receipt projection in the reproduction recipe. Independent
review passed 106 focused tests and both actual H replays reproduced the unchanged
report hash `53c5f901bcb71ba54886b6abea5f6e6a45e2015d7deb55dd6f10b1865f5bd186`.
No producer/package code or historical pins changed in that fix. All review
findings are resolved; exact-head hosted validation and protected delivery remain
separate from this completed local gate.

## Inherited late verifier correction

After the separate workflow PR received a late hosted finding, this batch
inherited `7910b0ab` through merge `f928a039c59ca73feaea11ef12710f2e9b2dd819`.
The public eight-stage verifier now redacts ordinary malformed-input/read
failures while preserving process interrupts. Independent review cleared
37 focused tests and both unchanged positive 34-file replay runs.

The full locked gate at `f928a039c59ca73feaea11ef12710f2e9b2dd819` exited 0:
6,517 tests, 98.0441% combined coverage, all schema/parity/mutation/hygiene
checks, CAS 645.22 MB/s, dependency audit, licence inventory, secret scan and
validated 112-component SBOM. No known local/review findings remain. Hosted
validation and protected merge remain separate; earlier runs above are retained.
