# Rust engineering guide

Rust is optional and is not part of the initial authoritative archive path.
Adopt it only for a measured hot path using the completed
`rust-adoption-template.md`.

Any Rust workspace must pin the stable toolchain, commit `Cargo.lock`, deny
warnings, forbid unsafe code by default, and pass:

```text
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace --all-features
```

Integrity or policy logic additionally requires property tests, mutation tests,
malformed-input tests, resource bounds, and equivalence tests against the
Python contract. Unsafe code requires a narrowly scoped design and safety proof;
it is not justified solely by performance.

Prefer a stable process/file boundary. Use PyO3/maturin only when benchmarks
show that an in-process boundary materially improves the measured workload.
Every failure maps to the documented CLI/state model without panics crossing
the boundary or partial objects becoming authoritative.
