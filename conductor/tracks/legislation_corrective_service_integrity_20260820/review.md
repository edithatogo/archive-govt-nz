# Review

## Review pass 1

- **High, fixed:** a cold source response of 304 could have been accepted as
  `no_change` without a prior cumulative manifestation. The service now fails
  that state closed and has a negative test.
- **High, fixed:** normalisation inherited an unconditional open-access rights
  disposition. New records now retain `rights_statement: null` and
  `redistribution_policy: rights_review_required` so the rights track remains
  unresolved.
- **Medium, fixed:** the cumulative v1 manifest changed its record hash field
  names. Compatibility aliases `raw_sha256` and `raw_blake3` are retained while
  canonical v2 record fields remain present.

## Review pass 2

- Correctness and state integrity: **Pass** after review fixes.
- Requirements SVC-M1 through SVC-M6: **Pass** in deterministic local tests.
- Product evidence and failure-label guidance: **Pass**; local, hosted,
  publication, rights, recovery, and cutover states remain separate.
- Technology-stack Python typing and locked-tooling guidance: **Pass**.
- General and Python style guides: **Pass** under repository Ruff and
  BasedPyright configuration.
- SVC-M7 command form: direct execution is blocked by the pre-existing tracked
  mode `100644`; the script's exact locked body passed through Bash. This
  limitation is recorded and does not change the service implementation.

## Review pass 3

- **High, fixed:** cumulative manifests and checkpoints accepted malformed or
  unauthenticated accounting state. Record and discovered-inventory roots are
  now independently recomputed and linked through the checkpoint.
- **High, fixed:** the same canonical manifestation identity could replace
  different source bytes. Manifest merges now reject byte or identity
  collisions and duplicate prior identities.
- **High, fixed:** partial batches could be recorded as completed and explicit
  generated identities could not retain conditional validators for a later
  304. Both state transitions now preserve resumability and provable no-change.
- **High, fixed:** monthly reconciliation trusted an unrooted discovered count.
  New manifests authenticate sorted unique discovered IDs and their exact
  denominator; old manifests fall back to their observed record identities.
- **Medium, fixed:** a deterministic CLI parser test made live publication
  readback requests. It now isolates parsing from the separately retained
  mocked verifier and negative-control tests; publication remains gated.
- Exact locked validation passed 690 tests with 95.79% coverage and all
  repository gates at implementation commit `84ca569`.

No unresolved code finding remains in this track. Hosted CI and merge remain
separate; the PR must stay unmerged under the active freeze.

PR #156 opened against current `main`; merge remains pending by design.
