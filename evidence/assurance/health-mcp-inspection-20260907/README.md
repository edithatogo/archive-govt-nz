# Read-only MCP workbook inspection

Isolated implementation from `042c69f3a968015359d4e4ada233f2c328d41a9c`.
Bounded Phase 8 / M-15 / AC-13 interface slice, not phase closure.

## Interface

`health_appropriations_inspect_workbook` requires `source` and lowercase
SHA-256 `expected_sha256`. It delegates to the existing CLI's `inspect_workbook`;
no adapter, CLI behavior or canonical schema is changed. Inventory only is the
MCP default (`rows=0`, `columns=12`). Explicit previews accept rows 0–20,
columns 1–50 and an optional worksheet name. Real integer inputs are required;
booleans and floating integral values are rejected before inspection. Unknown
arguments, including write flags, are rejected. Source and worksheet arguments
are bounded to 4,096 and 31 characters respectively.

Successful MCP content and structuredContent use the same JSON representation
as the CLI. Existing source byte, package, aggregate cell and preview-value
bounds remain authoritative. Formula text is not evaluated; decoded previews
are not canonical facts. Caller-selected source metadata/explicit preview cells
can be disclosed to the caller; the tool does not assert rights eligibility or
make arbitrary local workbook contents public-safe. No acquisition, source write,
derivative creation, publication, scheduling or resume execution is exposed.

The runtime schema is an exact semantic mirror of
`schemas/health-workbook-inspection-v1.schema.json`, with an equality regression.
Embedding it avoids relying on a repository-root file in installed distributions.
This adds no broader conformance claim. Input failures are constant redacted
JSON-RPC invalid-parameter errors; read/parse failures reuse the inspector's
redacted exception-class messages and MCP `isError=true` behavior.

## Proof

22 new synthetic cases. RED: the unknown tool failed the first requested
contract before implementation. Initial GREEN attempt exposed tuple/list wire
representation mismatch and missing input schema dialect; corrected by JSON
normalization and the existing 2020-12 dialect, not relaxed assertions.
Initial Ruff diagnostics were corrected; the standalone mutation recipe uses
the established implicit-package exemption only, with no coverage exclusions.

Final affected run: **380 passed in 5.45 seconds**, no warnings.
New binding: **18/18 statements, 2/2 branches, 100%**. All ten added executable
server lines are covered. Whole server: 260 statements, one previously existing
uncovered line (raw rebuild dispatch), 100 branches, one partial; scoped combined
coverage 99%. This is not a full-harness result.

Cold mutation: baseline exit 0, eight of eight targeted mutants killed with
pytest exit 1, no collection-error credit. Checks cover default previews,
worksheet/column selection, SHA binding, integer typing, input validation,
direct-call validation and protocol redaction. Final rerun after strengthening
the no-inspection guard also killed all eight. Ruff format/check, basedpyright
(0 errors/warnings/notes) and diff whitespace checks passed.

Use the existing locked Python environment with `PYTHONPATH=src`:

```sh
python -m coverage run -m pytest -q tests/mcp \
  tests/domains/health_appropriations/test_inspection.py \
  tests/domains/health_appropriations/test_budget_operations.py \
  tests/domains/health_appropriations/test_source_operations.py \
  tests/domains/health_appropriations/test_rebuild_completion.py \
  tests/cli/test_mcp_cli_contract.py
python -m coverage report --include='*/mcp_health_inspection.py,*/mcp_server.py'
python -B evidence/assurance/health-mcp-inspection-20260907/mutations.py
```

File SHA-256 pins:

| File | SHA-256 |
| --- | --- |
| src/archive_govt_nz/mcp_server.py | afaf224d490749a78fcf1c5bd2c42812baa33ca7e323c86009f456b36659cdc2 |
| src/archive_govt_nz/mcp_health_inspection.py | 835388fcd19c2b053a9e55353c1bc63059b2e365329aa750952b9f124f11148b |
| tests/mcp/test_health_inspection.py | 4a5a289b975eae3a9327a25db79bb362c706fa9cb74a24daa5689db50158bcfb |
| evidence/assurance/health-mcp-inspection-20260907/mutations.py | 5ff230a30452802d846184109600a0046774e27a7c055cc37014b23a01fd39ae |

All source fixtures are synthetic. Parent owns independent review, integration,
full harness and hosted checks. No shared lifecycle edits or remote mutations.
