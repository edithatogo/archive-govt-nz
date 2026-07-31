# Rust adoption evidence template

## Candidate

- Conductor task and GitHub issue:
- Exact Python baseline revision:
- Proposed Rust boundary:
- Data and fixtures:
- Hardware, operating system, and toolchain:

## Correctness and safety

- Contract/equivalence tests:
- Malformed and adversarial inputs:
- Memory, disk, time, and concurrency bounds:
- Panic and interruption behavior:
- Unsafe-code inventory and justification:

## Benchmark

Record commands, raw results, variance, warm-up, sample count, peak memory, and
I/O conditions. Compare end-to-end behavior, not an isolated favorable kernel.

## Decision

- Measured benefit:
- Added build, supply-chain, portability, and maintenance cost:
- Rejected simpler alternatives:
- Adopt, defer, or reject:
- Evidence receipt:

No Rust code is merged until this evidence demonstrates a material benefit and
the repository's Python and Rust gates both pass.
