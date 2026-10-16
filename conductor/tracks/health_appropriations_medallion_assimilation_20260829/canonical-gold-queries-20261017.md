# Canonical Gold named queries

M-10, M-13, M-15; AC-08, AC-11, AC-13. Related issues: #205, #212, #214.

The CLI command `health-appropriations-query-canonical-gold` and MCP tool
`health_appropriations_query_canonical_gold` read one of eight existing fact
products: historical, budget, revenue, pharmac, moh, crown_befu, crown_hyefu,
and fiscal_crown. Callers supply a local directory and an independently pinned
canonical Gold manifest, a product name, and a limit between 1 and 200
(default 50). The CLI defaults to historical; MCP requires an explicit product.
The receipt reports total/returned counts and truncation. This bounded interface
is not a complete export or a paging API.

The shared reader first verifies the entire declared package inventory/fixity,
then rehashes the manifest and selected payload. It checks the existing product
schema in its Parquet transport representation, including metadata, row counts
and non-nullable fields. A 64 MiB compressed payload, 100,000 input rows and
256 MiB estimated/decoded expansion limit apply. External column chunks are
rejected before materialization; dictionary/prefix expansion is conservatively
bounded. The existing verifier also limits package inventory and total bytes.

A fixed in-memory DuckDB query orders all columns ascending with nulls last.
External access and disk spilling are disabled, with one thread and bounded
DuckDB memory. There is no user SQL or source lookup. Decimal values use exact
strings; dates/timestamps use ISO 8601. The query result is restored to the validated
input Arrow schema, preserving UTC timestamps across host timezones. All source fields, identities, units,
vintages, qualifiers and Budget department/portfolio dimensions are retained.
Classification mapping, revision interpretation and cross-source comparison
remain explicitly unassessed/not performed, consistent with the package reports.
Pharmac budget scopes and funding regimes are not pooled. Published MoH measure
labels do not qualify their unknown denominator/unit definitions.

## Verification

The focused suite passed 18 tests, covering eight typed product fixtures,
exact values and identities, deterministic ordering, unchanged package bytes,
invalid pins/tampering/repinned schema and row-count drift, limits, closed MCP
arguments, actual CLI parsing and initialized MCP success/failure receipts.
Dictionary expansion and external column chunks are rejected before Arrow data
reads. Focused typing reported zero errors/warnings; relevant lint passed.

The neighboring verifier, Fiscal query, MCP and CLI integration checks passed
131 tests in 12.34s after the timezone fix. Two native Gold rebuilds from retained
inputs have identical inventories and file digests. Their shared manifest is
`2f14fa0930df65f10a835ffa261c920b7331d25c7e8fa72017243239e12084f8`.
Every returned native row matches independently decoded Arrow values exactly;
all eight products have identical direct-call, actual CLI-parser and initialized
MCP receipts, deterministic repeats and unchanged package files. The capped
historical/Budget readbacks verify returned subsets and exact total/truncation
counts, not all-row query coverage.

| Product | Stored rows | Returned rows | Truncated |
| --- | ---: | ---: | --- |
| budget | 341 | 200 | true |
| crown_befu | 10 | 10 | false |
| crown_hyefu | 10 | 10 | false |
| fiscal_crown | 61 | 61 | false |
| historical | 214 | 200 | true |
| moh | 80 | 80 | false |
| pharmac | 14 | 14 | false |
| revenue | 70 | 70 | false |

The package's classification report retains `mapping=not_inferred` and
`observed_rows_only`. The Budget revision report retains 93 shared unchanged
series/periods and zero changed candidates; Pharmac has no shared series/period
across vintages. Both remain `interpretation=not_assessed`. These report states
were read alongside the source-separated rows, not converted to approved
classification relationships or revision decisions.

Native artefacts are retained outside Git at
`/Volumes/PortableSSD/tmp/canonical-gold-query-20261017/`: the two packages under
`native/gold-first` and `native/gold-second`, `native/query-assurance.json`,
`native_readback.py`, and bounded execution/failure logs. Receipt SHA-256:
`aa6486d9ec8ef5572cbee51943d0487dc00e90493616a01be34f5669d407c50c`.
Readback script SHA-256:
`fba9fd4ef3bfd836d570d950cfca99ef5101d90c2acc9ed36828b551266a5362`.
Run the script with `uv run --locked python` from the repository. Native rebuild
setup reuses `tools.health_recovery_assurance.canonical_inputs` and the existing
source-bound `GoldInputs`; the completed output packages were preserved when
verification-script setup/status assertions failed.

The required `./scripts/validate.sh` passed on implementation commit
`ff91c196c3fd9c81d3cbec186a7ca64d259100cf`: 7,693 tests passed, 10 skipped;
97.39% coverage against the 80% floor; 56 schemas/46 representative documents;
parity 9/9; all mutation, hygiene, security and supply-chain gates passed,
including the 113-component SBOM. Conductor reports 93 tracks and no errors.
The external durable `validation.log` and `validation.exit` record exit 0.
The follow-up commit records this evidence only; hosted checks must qualify
the final PR head before merge. Native builds use
retained canonical/Silver packages with existing source-byte revalidation; this
is not fresh source retrieval or a full Bronze normalization/recovery claim.
No rights approval, publication, source completeness, cross-family economic
equivalence, or whole-track completion is asserted.

Example invocation (substitute the actual local package directory and its pin):

```sh
archive-govt-nz health-appropriations-query-canonical-gold \
  /absolute/path/to/gold MANIFEST_SHA256 --product budget --limit 50
```
