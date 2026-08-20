# Evidence

- Independent review of merged PR #150: ASW rejected at merge commit
  `fefa36d`.
- Local successor base: `580a134`, the exact green head of open PR #156.
- Functional correction commit: `7616ddba314900e6563f4feafa62905276477486`.
- Red evidence: 11 of 11 adversarial tests failed against the inherited PR #150
  implementation before the correction.
- Focused validation: Ruff passed, BasedPyright reported zero errors and zero
  warnings, and 103 affected tests passed.
- Full validation: `bash scripts/validate.sh` passed with 733 tests and 95.87%
  branch-aware coverage. `cli_integrity.py` reached 100% line and branch
  coverage. Schema, mutation, hygiene, CAS benchmark, audit, licence, secrets,
  and SBOM gates passed.
- No global CLI successor PR has been opened.
- Publication authority, redistribution rights, and donor archival remain
  pending.
