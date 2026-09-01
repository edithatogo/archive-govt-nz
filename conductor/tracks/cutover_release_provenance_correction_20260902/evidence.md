# Evidence

## Repository identities

- Target baseline: `740389b7420ea7ba7382d40a23ad3e23ba2c680a`.
- Archived donor head: `b40587f1b1aec7356a0f623916fcc8212397d283`.
- Release tag commit: `949f6f6abed0cfb668fc5f163129f11e54f335a3`.

## Verified cycle chains

- Cycle 1: harvest `32625516235`, reconciliation `32625566353`, recovery `32625612739`.
- Cycle 2: harvest `32625990438`, reconciliation `32626071396`, recovery `32626113799`.

The typed correction receipt records each run's hosted URL, head commit, status,
job, artefact, timestamps, and receipt hash.

## Public release correction

- GitHub release ID: `375146205`.
- Original body SHA-256: `812b5d997a193e37abf21fcf22df7a8ec872efa8407eb29a4f70501e7fb540c6`.
- Corrected body SHA-256: `66617b06cce61d19b3a2dadc4e352d32af9292334bb9cae4379a82147fcfd28d`.
- Post-edit public GET raw response SHA-256: `dd9a0d71aa8356a5c33cf4134a19d40ff01f38f2a3e3749b33650f7259f2063a`.
- Post-edit normalized response SHA-256: `fff93e36259836c84c602944b8bbaa079373226449214b44ebf8acde376f75d1`.
- Readback timestamp: `2026-09-01T16:43:42Z`.
- Readback ETag: `W/"ce56368ebdf86cefa385be27bc6b40e1310140fcf77b1f8f394015700909b0fa"`.

The original body remains an exact prefix of the corrected body. The release
still has no assets, and its tag, name, publication timestamp, draft,
prerelease, and immutability states are unchanged.

## Validation

- Focused tests: 19 passed.
- Critical-code coverage: 100% line and branch.
- Targeted mutation gate: 10/10 killed.
- Schema lane: 47 schemas and 37 representative documents valid.
- Ruff and Pyright: passed.
- Complete assurance gate: 4529 tests passed with 97.50% aggregate coverage;
  all repository mutation, parity, supply-chain, secret, licence, and SBOM lanes
  passed. The standard auto-worker attempt is preserved in the run log with
  its host-load deadline flake; the unchanged one-worker gate passed.
