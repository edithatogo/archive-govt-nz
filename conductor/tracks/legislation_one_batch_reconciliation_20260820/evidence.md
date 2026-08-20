# Evidence

- Current invalid generator:
  `tools/generate_executable_legislation_parity.py`.
- Generated false-positive receipts retained under
  `evidence/migrations/corpus-legislation-nz/parity/` pending explicit
  invalidation metadata.
- Live donor observation on 2026-08-20: repository unarchived, zero issues, and
  `seeds/reviewed/historical-work-ids-0001.txt` present at Git blob
  `6d88b24a2c79c156841dff796bbf47d5b13f0528`, size 8,987 bytes. Its donor
  README says 500 work IDs and explicitly disclaims completeness.
- This branch and all validation are local-only. No real batch has executed.

## Corrected-stack validation

- Stacked base: workflow correction `34d347a` (including service, global CLI,
  legislation CLI, stable MCP, and hosted workflow gates).
- Focused command: 77 adversarial one-batch tests passed; critical module
  coverage was 228/228 statements and 106/106 branches (100%).
- Full command: `bash scripts/validate.sh` exited 0; 850 tests passed at 95.89%
  overall coverage; 22 schemas and 12 representative documents validated; all
  mutation, hygiene, CAS benchmark, direct dependency audit, licence, secret,
  and SBOM gates passed.
- Generated validation timestamps and donor snapshots were restored rather than
  committed as execution evidence.
- Post-rebase exact harness: 852 tests passed at 95.87% branch-aware coverage;
  22 schemas and 12 representative documents plus every remaining repository
  gate passed. No real batch was executed.
- Current-main validation on workflow squash merge `6839d7b`: 77 focused
  adversarial tests passed with the reconciliation module at 100% line and
  branch coverage. The full locked harness passed 858 tests at 96.35%
  branch-aware coverage and every remaining repository gate. No real batch was
  executed; the execution gate remains pending.

## Real-batch preflight

- One-batch reconciler PR #162 merged as `c2ad3fe` with all required checks,
  dependency review, and Codecov patch green.
- Authoritative donor batch `historical-work-ids-0001.txt` was read from donor
  Git blob `6d88b24a2c79c156841dff796bbf47d5b13f0528`: 500 lines, 8,987 bytes,
  canonical SHA-256
  `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
- A bounded live discovery request for the first identity returned HTTP 401.
  The prior client incorrectly converted every non-200 response into an empty
  inventory. Commit `52ec2c8` now reports this as `status=failed`, exit 2, and
  also rejects malformed HTTP 200 payloads.
- Forty-two focused API/CLI tests passed. The first full harness attempt hit
  the fixed 300-second test limit at 88% with no test failure; the exact warmed
  rerun completed 864 tests at 96.37% coverage and every remaining gate.
- `LEGISLATION_API_KEY` is absent locally and no repository Actions secret with
  that name is configured. No target state or passed reconciliation receipt was
  created. Real-batch execution remains blocked and pending.
