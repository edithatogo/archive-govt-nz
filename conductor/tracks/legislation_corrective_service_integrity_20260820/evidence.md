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
- Review-fix phase I: 38/38 affected tests passed; focused Ruff and BasedPyright
  passed.
- Review-fix phase II: the final affected suite passed 83/83 tests, including
  fail-closed malformed-state, identity-collision, inventory-authentication,
  checkpoint-linkage, partial-batch, explicit-target, and 304 controls.
- Review-fix phase III: 86/86 affected tests passed, including empty work and
  duplicate supplied expression/manifestation identity negative controls.
- Full locked harness: 693/693 tests passed with 95.76% coverage; schema,
  mutation, hygiene, CAS benchmark, dependency audit, licence inventory,
  secret scan, and SBOM gates passed. This is local validation only.
- The tracked `scripts/validate.sh` mode is `100644`, so direct execution
  returned `permission denied`; `bash scripts/validate.sh` executed the exact
  locked harness body successfully.
- The executable service and monthly reconciliation defaults contain no fixed
  33,693 denominator. The separate parity generator remains pending replacement
  in the workflow/reconciliation gate and is not evidence for this PR.
- Initial corrective implementation commit: `e70a70d`.
- Review-hardening implementation commit: `84ca569`.
- Target-identity hardening implementation commit: `84d8562`.
- Corrective PR: [#156](https://github.com/edithatogo/archive-govt-nz/pull/156),
  open and unmerged at track closeout.
