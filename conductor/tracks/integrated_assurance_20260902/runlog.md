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
- 2026-09-03: Hosted run `33740682306` failed closed on Ubuntu, macOS, and
  Windows after the credential scanner found one candidate in the new receipt:
  the metadata key `secret_scan`. The failure is retained. The receipt now uses
  `credential_scan`, and the two API readbacks are deterministic projections
  that omit only opaque `node_id` and redundant `_links` values while retaining
  the original response hashes. No scanner exclusion or threshold changed.
- 2026-09-03: The first focused regression attempt applied projection-only
  assertions to the enclosing receipt as well and failed because the receipt
  names the deliberately excluded fields. The corrected test limits structural
  minimization assertions to the two projections and scans all three evidence
  JSON files for credential candidates.
- 2026-09-03: The second focused attempt called `detect-secrets` without the
  repository's standard receipt-line exclusions and correctly detected a
  receipt SHA-256 as high entropy. The final test imports the production
  exclusion contract, so it exercises the same strict scanner semantics as the
  assurance harness rather than a different command.
- 2026-09-03: A third focused attempt imported the repository-root `tools`
  directory as a Python package and failed collection because it is not one.
  The corrected test adds the tools directory itself to the import path before
  importing the production scanner constant.
- 2026-09-03: The first full harness stopped at lint because the new focused
  test lacked required docstrings and used an unresolved executable path. The
  test now documents its contract and resolves `detect-secrets` explicitly;
  no lint or security rule was suppressed.
- 2026-09-03: The next harness passed lint and then stopped at typing because
  the tools-directory import was intentionally invisible to static resolution.
  The test now loads the production scanner constant through `runpy` with an
  explicit type assertion, preserving static analysis without duplicating the
  exclusion expression.
- 2026-09-03: A focused static check required `runpy.run_path`'s path argument
  to be an explicit string. Converting the repository `Path` to `str` resolved
  the type error without changing scanner behavior.
