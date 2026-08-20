# Evidence

## Local validation

- Focused command covered workflow gates, bounded harvest, authenticated
  reconciliation, sharded recovery, archive service, and legislation CLI.
- Result: 103 tests passed.
- Schedule contract v1.1 validated successfully.
- `bash scripts/validate.sh`: exit 0; 773 tests passed at 95.72% coverage;
  format, lint, types, schemas, all mutation lanes, hygiene, CAS benchmark,
  direct dependency audit, licences, secrets, and SBOM passed.

## External boundary

Every hosted legislation job exits 3 before checkout. No workflow, live source
batch, artifact upload, publication, rights action, recovery claim, cutover, or
donor archive was executed.
