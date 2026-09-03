# Run log

- 2026-09-02: Bound clean worktree to target `dd90f8ec...`, issue #351, and
  archived donor `b40587f...`.
- 2026-09-02: Native 31-stage harness passed with 4,543 tests and 97.50%
  project coverage. Additional restoration/readback/evidence mutation suites
  killed every mutant; reproducible builds matched byte for byte.
- 2026-09-02: Exact-main cross-platform CI completed successfully. Live
  security readback found two open high-severity CodeQL alerts; actionlint found
  two SC2086 failures. Opened #352 and #353 without absorbing their fixes.
- 2026-09-02: Hosted policy readback found no branch protection or applicable
  ruleset on `main`; opened #354. Track remains incomplete.
- 2026-09-03: Under explicit maintainer authorization, GitHub ruleset
  `22180861` was read back through its direct endpoint and the repository
  ruleset listing. Both responses identify the active `main-integrated-assurance`
  rule for `~DEFAULT_BRANCH`; exact responses and hashes are preserved under
  `evidence/assurance/main-ruleset-20260903/`. The update supersedes issue
  #354's missing-enforcement finding while preserving the original evidence.
- 2026-09-03: `./scripts/validate.sh` passed on the scoped evidence update:
  4,575 tests, 97.52% project coverage, 48 schemas, 38 representative
  documents, every repository mutation lane, dependency audit, licence
  inventory, secret scan, and 111-component SBOM validation.
