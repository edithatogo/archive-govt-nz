# Local resume interfaces — 2026-09-07

Base: `8af668f50509efd4dd2ed9f90ac568eba4998898`; isolated branch
`codex/health-resume-interfaces-20260907`. Bounded Phase 8 / M-15, M-18 /
AC-13, AC-16 interface slice; not phase closure. Existing native planner,
executor, verifier, adapters and the workbook-inspection interface are unchanged.

## Commands and authority

`health-appropriations-plan-resume` delegates to `plan_resume`. Mandatory flags:
`--donor-manifest`, `--donor-manifest-sha256`, `--previous-run`,
`--previous-plan-sha256`, `--store-root`, `--observed-at`. Optional repeated
`--stage-pin stage=SHA256` accepts at most the four existing profile keys
(budget, historical, befu, hyefu), without duplicates or last-wins coercion.
Omitted stage pins remain unpinned, not implicitly reusable. MCP uses the
equivalent required `stage_manifest_sha256` object, which may be empty.

Success prints the native plan JSON without a command envelope. Saving stdout
and supplying its exact SHA-256 to the executor is tested. Saving that output
is an explicit caller action, not a planner filesystem write.

`health-appropriations-resume` requires the same inputs plus `--resume-plan`,
`--resume-plan-sha256`, and `--output-dir`. Its default is dry-run; only explicit
`--no-dry-run` permits the native executor to create one new exclusive local
attempt. Existing output is rejected, never overwritten. The executor rechecks
the saved plan and source context; the wrapper does not implement alternate
retry, copying, fixity or reconstruction logic. Partial attempts/failure markers
remain available; interrupts propagate. A failed invocation is not auto-retried.

`health-appropriations-verify-resume --attempt PATH --store-root PATH
--receipt-sha256 SHA256` delegates only to `verify_resume`. Its pin identifies
RESUME_RECEIPT.json, not the child MANIFEST.json. It verifies the saved envelope
and child without revisiting old-attempt state, planning or execution.

Read-only MCP tools are `health_appropriations_plan_resume` and
`health_appropriations_verify_resume`. They share the closed input shapes and
native receipts with the CLI. There is no MCP executor, dry-run switch or output
directory on these tools. Their output schemas identify the native receipt
families; native APIs retain responsibility for detailed stage validation.

Paths/text are bounded to 4,096 characters, pins are lowercase SHA-256, unknown
arguments and nonboolean executor flags are rejected before native dispatch.
CLI operation failures emit constant JSON with status failed/error
invalid_resume_operation and return 2. MCP invalid arguments are constant
invalid-parameter errors; native failures are constant tool-error results.
Successful source-plan provenance is intentionally retained; source diagnostics
and supplied private strings are not included in failure messages.

No rights approval, publication, capture, schedule, automatic repair, new source
adapter or semantic promotion is introduced. Verification preserves the native
scope and rights/publication qualifications rather than inventing readiness.

## Validation

22 new synthetic cases. RED was missing resume_operations import (collection
exit 2) before implementation. First test run encountered Cyclopts' normal
SystemExit return handling; tests now explicitly request return_value while
retaining the actual CLI parser. The first MCP run caught omitted output-schema
dialect declarations, which were added. Initial import/style/type diagnostics
were fixed without relaxing validators or adding coverage exclusions.

Final affected selection: **275 passed in 17.98 seconds**, no warnings.
New operations module: **65/65 statements, 14/14 branches, 100%**.
All seven added executable registration/dispatch lines in CLI/MCP are covered.
The existing large registration modules are not claimed to have full coverage.

Tests cover CLI/API/MCP plan parity, actual CLI argument parsing, exact stdout
plan reuse, no-write defaults, explicit exclusive execution, independent receipt
verification, wrong/stale pins, collisions, nonboolean flags, repeated/duplicate
stage options, protocol redaction, retained partial attempts and interruption.
Planner/executor spies prove verification does not invoke them; invalid-input
tests prove rejection occurs before native calls. Originals remain unchanged.

Cold bounded mutation: baseline exit 0; **11/11 killed with pytest exit 1**,
no collection-error credit. Initial input-contract removal survived because
native argument checks masked it; an independent pre-dispatch regression now
kills it. Removing the stage-count guard also survived: uniqueness plus the
four-member allowlist already prevent a valid fifth stage. The final runner
instead tests the meaningful off-by-one boundary, with acceptance of exactly
four valid pins. This mutation-target change is explicit, not evidence that
the redundant guard's removal was killed. No production guard was weakened.

Ruff check/format, focused basedpyright (0 errors/warnings/notes), and
git diff --check passed. The standalone mutation recipe uses only the existing
implicit-package exemption; no threshold, test exclusion or dependency changes.
The new operations module is 213 nonblank/noncomment lines; CLI/MCP changes
are registration and dispatch only.

## Reproduce

Use the existing locked sibling environment with `PYTHONPATH=src`:

```sh
python -m coverage run -m pytest -q \
  tests/domains/health_appropriations/test_resume_operations.py \
  tests/domains/health_appropriations/test_resume_execution.py \
  tests/domains/health_appropriations/test_rebuild_resume.py \
  tests/mcp tests/cli/test_mcp_cli_contract.py
python -m coverage report --include='*/resume_operations.py'
python -B evidence/assurance/health-resume-interfaces-20260907/mutations.py
```

SHA-256 pins:

| File | Digest |
| --- | --- |
| src/archive_govt_nz/domains/health_appropriations/resume_operations.py | a29cf777dc5c6f561e0b4e2a0384ce9fabd973d7c0fad9143c582a9648532525 |
| src/archive_govt_nz/cli.py | 04c418070332a358794ebfd46128f03598a3edbd1cd5659a14093b92c44f5ca6 |
| src/archive_govt_nz/mcp_server.py | 436e12e37aab6f7580266c3dfb2ea9a704bab6423fe32f36914f635ff73d5d83 |
| tests/domains/health_appropriations/test_resume_operations.py | 201b0cd91ef0d47ddfdc09e85b3ceb7f3d6f5c8fa01eb38f3c0d7da0449cdc18 |
| evidence/assurance/health-resume-interfaces-20260907/mutations.py | 5ca0c3ab775e1cd022213649f4567ac7eb77ece345ffc2d6413a88ab74ecfb7f |

No full gate, hosted checks, live source execution, lifecycle edits or remote
mutations. Parent owns independent review, integration and full assurance.
