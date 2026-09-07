# Health extraction integration

The first full gate at `5dfa297a17d8fed4eca884ac57ad08eead9126cf`
passed lock, Conductor state, format and lint, then failed typing with 20
diagnostics in the donor-detail synthetic tests. `Workbook.active` can be
absent or a chartsheet in the installed stubs. Five explicit `Worksheet`
assertions establish the synthetic fixture contract without suppressing errors
or changing production behavior. Tests and later full-harness gates were not
reached in this attempt.

The corrected full gate at `70cd15b0` exited 0: 6,137 tests passed, coverage
remained above 95%, and all configured schema, parity, mutation, hygiene and
supply-chain checks passed. CAS throughput was 664.65 MB/s against a 25 MB/s
minimum; the validated SBOM contains 112 components. The five fixture type
assertions also passed a targeted type check and all 27 donor-detail tests.
The subsequent parent merge adds only the completed interface validation
receipt; it does not change the tested implementation.

Independent reviews cleared the exact 160 donor detail amounts, 20 excluded
formula totals, 69 revenue facts with all 1,000 row dispositions and 1,104 lineage
records, and the mock-only canonical FOI publication opt-in. The direct pytest
reviews reproduced retained-source hashes, output idempotency and unchanged
originals. These reviews remain separate from the required corrected full gate.
