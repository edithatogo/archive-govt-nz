# Evidence

Current evidence is bounded to live GitHub state and local repository
inspection. No service correction, real batch, canary, publication, rights,
recovery, cutover, or donor-archival completion is claimed yet.

- PRs #150-#155: observed merged on 2026-08-20.
- `edithatogo/sm-govt-nz`: observed archived, then verified unarchived at
  2026-08-20T06:32:24Z.
- Local `main`: clean and equal to `origin/main` at `3b38d10` before branching.
- Red phase: 10 expected failures and 26 passes in the bounded affected suite.
- Green phase: 37/37 affected tests passed; focused Ruff and BasedPyright
  passed.
- Review-fix phase: 38/38 affected tests passed; focused Ruff and BasedPyright
  passed.
- Full locked harness: 643/643 tests passed with 95.22% coverage; schema,
  mutation, hygiene, CAS benchmark, dependency audit, licence inventory,
  secret scan, and SBOM gates passed. This is local validation only.
- The tracked `scripts/validate.sh` mode is `100644`, so direct execution
  returned `permission denied`; `bash scripts/validate.sh` executed the exact
  locked harness body successfully.
- The executable service and monthly reconciliation defaults contain no fixed
  33,693 denominator. The separate parity generator remains pending replacement
  in the workflow/reconciliation gate and is not evidence for this PR.
- Corrective implementation commit: `e70a70d`.
- Corrective PR: [#156](https://github.com/edithatogo/archive-govt-nz/pull/156),
  open and unmerged at track closeout.
