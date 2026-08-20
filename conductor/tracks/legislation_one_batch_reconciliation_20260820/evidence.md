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
