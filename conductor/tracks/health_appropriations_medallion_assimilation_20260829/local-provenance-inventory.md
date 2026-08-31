# Local metadata and replay gap: bounded proposal

Inspection only; no descriptor, candidate, upload or rights grant was generated.

## Existing helpers are not a current-product metadata acceptance gate

`tools/build_health_candidate.py` bundles copy, rights-filtering and publication-
shaped metadata/card generation. Its card asserts CC-BY-4.0. Do not invoke it on
the new raw-replay outputs. `schemas/medallion.py` health-domain metadata uses
UND rights status (appropriately unresolved) but its field list is the legacy
domain-wide shape, not the exact set of physical source-specific and canonical
recordsets now produced. Its default public identifiers/distribution semantics
also require review before treating output as a local-only product description.

`schemas/health_recordsets.py:recordset_schema` provides immutable versioned
canonical physical schemas, explicitly structural-only. It is reusable for
field descriptions/fingerprints, not semantic closure or source rights. CPI,
QES, Ministry, GDP and original source-native facts must be described with their
actual adapter schemas, not silently advertised as canonical spending records.

## Smallest next pure local metadata slice

Accept explicit already-verified typed product descriptors rather than paths or
an implicit registry scan: package pin, original SHA, profile/vintage, relative
product name, layer/recordset role, row count, physical schema fingerprint,
payload hash and byte count, and input-product dependencies. Produce a canonical
JSON local inventory with stable source-to-product edges and exact per-field
Arrow type/nullability/metadata. Use content-addressed local identifiers rather
than invented public download URLs. Do not embed timestamps, local absolute
paths, file contents, external credentials or source text in IDs.

Every product starts `rights_state=not_evaluated`, `publication_state=local_only`,
`approval=not_granted`; any separately supplied hash-bound rights observations
must remain observations, not synthesized eligibility. No blanket licence,
publication date, federation equivalence or completed recovery assertion.
Input fixity should be explicitly outside a pure helper; a separate composed
reader can establish it later. Unknown profiles/schema mismatches, duplicate
identities, missing dependencies and ambiguous rights joins fail closed.

## What remains before full Platinum/recovery acceptance

- Red-first contracts for deterministic descriptor output and mixed/unresolved/
  conflicting rights; exact field-schema coverage across each actual product.
- Explicit mappings into DCAT/Croissant/RO-Crate/PROV with validators; no claim
  that a local JSON inventory alone satisfies these standards.
- Clean empty-derivative replay must produce this same pinned local metadata
  from Bronze + code + parameters, alongside Silver/Gold/SQLite/plots/reports.
- Compare bytes or explicitly reviewed rendering differences, prove no original
  changes, and test interrupted/resumed/partial outputs and missing inputs.
- Federation remains separate and requires approved namespace/version/mapping
  evidence; no counterpart repository or live-runtime dependency is invented.
- Rights-filtered candidate assembly, exact-manifest approval and independent
  hosted readback remain separate after local replay; current replay excludes
  Platinum and must not close the whole Phase9 recovery checkbox.

## Bounded implementation now approved

Initial scope is canonical historical Health/GDP and Budget classification only:
`health_spending_fact`, `fiscal_context_fact`, `field_lineage`,
`classification_dimension`. Initial missing-module test collection failed red
before production implementation. This pure descriptor helper does not compose
disk readers or establish input fixity, semantic truth or metadata replay.

The closed profile/vintage pairs preserve actual retained spellings:
`historical-health-gdp-canonical/v1` with `fiscal-2024` or
`Fiscal-Time-Series-1972-2025`; `budget-functional-classification-source-label/v1`
with `Budget-2025` or `Budget-2026`. Source nodes use original SHA identifiers;
product dependencies use package-pin/path keys. Product IDs explicitly cover
descriptor metadata, not a recursive transitive dependency-ID hash. Schema and
field metadata are represented as lossless hex bytes. No field values are read.

Independent review identified impossible file/directory prefix collisions and
requested explicit field-metadata and ID-scope declarations. Three regression
cases failed before correction. Casefolded prefix collisions now fail closed;
the bounded comparison also handles interleaved path sorts. Final independent
parent re-review found no further actionable issue.

Local validation: 52 tests, 100% critical coverage (92 statements/14 branches),
Ruff and basedpyright pass. Cold mutation killed all 70 generated mutants, zero
survivors/errors/timeouts/pardons/cache hits, 50.09 seconds; report SHA256
`1c18c142d86681f2e77c9f98be83415aff7daa159de24e448ed6365413092c7a`.
Source SHA256 `a1bdbe086bd572e97e73ec8babecbe8a5841bf4c917212f6daa4bfecb841b40d`;
test SHA256 `e49b415921a76f371d6eec7c099c18d8b23187d6f825ec6e2f3b62f406b589e4`.
Full native validation and hosted delivery are still pending at this checkpoint.

Separately, classification exporter PR316 was merged by this agent after all
seven required checks passed on exact head
`2b69abd890a8468f766fdb731f81af0060482490` with fresh clean/mergeable status.
The exact-head REST merge succeeded, and readback confirmed merge
`2400a9a4e650f4ed8098cd429d78478487be4602` at `2026-08-31T16:40:49Z`.
This is code delivery and local retention evidence, not publication approval.

### Pre-correction native checkpoint

Full native validation passed at `e73285e` with source `a1bdbe08...`:
3598 tests, eight existing ResourceWarnings, 102.03 seconds and 97.23% coverage;
all subsequent gates passed, including 42 schemas/32 documents, 9/9 parity,
324.21 MB/s CAS throughput, dependency/secret/licence checks and 111-component
SBOM. Log SHA256:
`204e1025ef089815290a69b75978980095f0f3327bf554358d02f711133dce29`.

During the frozen native tail, self-review identified a substantive graph-ID
alias: source byte hashes and product descriptor hashes shared `sha256:` IDs.
A caller could compute one product ID then use its digest as another product's
asserted source hash, yielding ambiguous cross-kind identifiers. This passed
test run is retained as pre-correction evidence, not final acceptance. Parent
approved disjoint `source:sha256:` and `product:sha256:` namespaces with a red
regression and renewed focused, mutation and full native assurance.

The new adversarial fixture reproduced the exact cross-kind intersection before
the three namespace changes. Corrected source SHA256
`be15bf09752530eebd7c33c748d3ceb760d90f8a60f6026c7e01f3b00c13490f`
and test SHA256
`8f67ccc4fea4b747c292e5ce5fcdf02aff2f8186276b599d1e4ee83b10534532`
pass 53 tests with 100% critical coverage (92/14), Ruff and typing. Renewed cold
mutation killed 70/70 with zero survivors/errors/timeouts/pardons/cache hits,
59.32 seconds; new report SHA256
`35c4bdc520093b8bbd6101d61e682a1e7cc8008f5d53e233a98b15bb852ec947`.
The prior native and mutation reports remain retained separately.

### Corrected native assurance

The required native harness passed with exit zero at corrected commit `e307bb8`:
3599 tests, eight existing ResourceWarnings, 79.25 seconds, 97.23% coverage;
42 schemas/32 representative documents, 9/9 parity, all mutation and hygiene
gates, 497.27 MB/s CAS throughput, dependency audit, licence and secret checks,
and 111-component SBOM. Corrected full log SHA256:
`2075dc38ec13f6b3e5cdb6d7da801d0bab7be740f70b9819bbaebf98c4aac001`.
No source/original/publication bytes changed. The native suite's two unrelated
timestamp-only generated fixtures were restored after the process completed.
Hosted checks and later integration remain separate observations.

Root independently re-reviewed the corrected typed namespaces and regression;
no additional finding. A second agent read the preceding full module/tests and
found no other issue within descriptor-only scope.

### Related hosted delivery observations

Parent/root performed PR309's exact-head merge after all seven fresh checks
passed with clean status at `576c999803944b46ec4737ffa6b9234709e78371`.
REST merge/readback confirmed `550b263254d039be4e857a561e56eb7afd9aa7cf`
at `2026-08-31T16:52:09Z`. Method `merge` preserved stack ancestry; no hosted
rule was changed. Parent similarly performed PR315's exact-head merge after
seven fresh successes and clean status at
`10731ff4b37f41365eb35eeb49dd37e957c74647`; readback confirmed
`76295f76c235a1c667b08334382795e78f949ae3` at `2026-08-31T16:57:36Z`.
These are parent-reported hosted receipts, not this agent's merge operations.
