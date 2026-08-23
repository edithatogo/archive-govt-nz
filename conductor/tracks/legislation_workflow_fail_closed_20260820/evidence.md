# Evidence

## Local validation

- Focused command covered workflow gates, bounded harvest, authenticated
  reconciliation, sharded recovery, archive service, and legislation CLI.
- Result: 103 tests passed.
- Schedule contract v1.1 validated successfully.
- `bash scripts/validate.sh`: exit 0; 773 tests passed at 95.72% coverage;
  format, lint, types, schemas, all mutation lanes, hygiene, CAS benchmark,
  direct dependency audit, licences, secrets, and SBOM passed.
- Post-rebase exact harness on MCP head `58cd63d`: 775 tests passed at 95.70%
  branch-aware coverage; every repository gate passed.
- Current-main validation on MCP squash merge `086eb4f`: 26 focused workflow
  and tool tests passed. The exact full harness passed 781 tests at 96.20%
  branch-aware coverage and every repository gate.

## External boundary

Every hosted legislation job exits 3 before checkout. No workflow, live source
batch, artifact upload, publication, rights action, recovery claim, cutover, or
donor archive was executed.
