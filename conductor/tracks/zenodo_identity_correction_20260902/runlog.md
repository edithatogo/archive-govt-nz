# Run log

- 2026-09-02: fetched target main `0158b46265cf2468d04e9aa3322d10f33674ee2c`; confirmed archived donor at `b40587f1b1aec7356a0f623916fcc8212397d283`.
- 2026-09-02: created issue #343, branch `codex/zenodo-doi-identity-correction`, and isolated worktree.
- 2026-09-02: retained new-version publication as a pending external gate; read-only audit and repository correction continue.
- 2026-09-02: live read-only audit verified concept record `20592539` redirects to the sole version record `20592540`; downloaded and hashed all three public files. No external write occurred.
- 2026-09-02: focused Prompt 16 suite passed 80 tests; critical Zenodo modules reached 100% line and branch coverage; targeted identity and publication mutation suites killed 10/10 mutants.
- 2026-09-02: first full harness attempt failed typing in the new test fixture; corrected in `91f870d` and recorded rather than restated as success.
- 2026-09-02: next full attempt reached the secret scan and found three high-entropy MD5 verification values in the new receipt; replaced redundant values with explicit verification booleans in `48af6de`; the standalone secret scan then passed.
- 2026-09-02: a later full attempt encountered an unrelated Hypothesis 200 ms deadline flake in `test_any_appended_object_bytes_invalidate_state`; the exact focused test passed on immediate reproduction without changing or weakening it.
- 2026-09-02: final `./scripts/validate.sh` passed: 4,472 tests, 97.50% total coverage, all schema/parity/mutation/supply-chain lanes, licence inventory, secret scan, and SBOM.
- 2026-09-02: no meaningful release was proposed. New-version publication gate was not triggered; no Zenodo draft, mutation, mint, or publication occurred.
