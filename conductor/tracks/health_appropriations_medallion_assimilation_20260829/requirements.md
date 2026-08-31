# Requirements: New Zealand Health Appropriations Medallion Assimilation

Requirements use MoSCoW priorities. Must requirements cannot be silently
weakened or deferred. Acceptance criteria are defined in `spec.md`.

## Must

### M-01 — Pinned donor identity and complete inventory

Freeze the donor commit, tree, deterministic Git archive digest and complete
23-path inventory. Detect missing, extra, renamed, or byte-changed files.

**Acceptance:** AC-01, AC-03.

### M-02 — Complete source census and disposition

Inventory the seed corpus, direct official expansion and selected contextual
series at a declared cutoff. Assign every discovered item a captured,
unchanged, superseded, unavailable, withdrawn, restricted, corrupt, retryable,
duplicate, or out-of-scope disposition with evidence.

**Acceptance:** AC-02, AC-03, AC-09.

### M-03 — Zero-loss Bronze preservation

Retain every donor file and acquired official original byte-for-byte in
content-addressed storage outside Git. Originals include source payloads,
donor code/docs, its SQLite derivative and all plots.

**Acceptance:** AC-01, AC-02, AC-12.

### M-04 — Bronze fixity, provenance and rights receipts

Record interoperable fixity, content identity, observation/retrieval context,
source revision, rights evidence, failure state and lineage. Validate manifests
and preserve material HTTP exchanges.

**Acceptance:** AC-04, AC-14, AC-16.

### M-05 — Dedicated health-appropriations Silver domain

Implement typed, versioned schemas for source inventory, appropriation,
health-spending, fiscal-context, pharmaceutical-budget,
price/population, classification and field-lineage record sets. Do not decode
binary workbooks through a generic text normalizer.

**Acceptance:** AC-05, AC-11.

### M-06 — Temporal, vintage, unit and classification semantics

Preserve financial-year meaning, source vintage, valid and observation time,
amount type, nominal/real status, currency/unit, base period, denominator,
source label, normalized identifier and classification drift.

**Acceptance:** AC-05, AC-09, AC-10.

### M-07 — Loss-accounted extraction and field lineage

Inventory every donor workbook sheet and detected table/range. Normalize each
in-scope data area or attach a reason-coded exclusion. Link every extracted
field to its original object and sheet/page/row/cell/range.

**Acceptance:** AC-03, AC-05.

### M-08 — Donor data parity and repair ledger

Reconcile all five donor SQLite tables and 312 rows. Preserve donor values as
an observed derivative and record every intentional correction as a row-level,
test-backed deviation rather than silently normalizing it away.

**Acceptance:** AC-06, AC-11.

### M-09 — Donor functional parity

Provide tested equivalents for workbook inspection, raw-to-structured
processing, SQLite export, all four analysis families, structured summaries
and six plots. Regression-test the donor compile failure and discovered
semantic defects.

**Acceptance:** AC-07, AC-08.

### M-10 — Rebuildable canonical and compatibility products

Make versioned Parquet the canonical tabular derivative, queryable with
DuckDB. Generate SQLite, plots, reports, catalogue and publication packages
from canonical layers with deterministic manifests.

**Acceptance:** AC-08, AC-12.

### M-11 — Direct longitudinal official expansion

Incorporate retrievable Vote Health Estimates/Supplementary Estimates, annual
Budget expenditure/revenue workbooks, BEFU/HYEFU expense and forecast data,
Treasury historical fiscal series, Ministry of Health Vote Health series and
Pharmac Combined Pharmaceutical Budget data, preserving explicit gaps.

**Acceptance:** AC-02, AC-09, AC-11.

### M-12 — Official analytical context and defensible measures

Incorporate rights-eligible CPI, wage, population, GDP and total/core Crown
expense series needed for real, per-capita and share measures. Each result
must identify the exact numerator, denominator, base and vintage.

**Acceptance:** AC-10, AC-11.

### M-13 — Gold analytics and deterministic visualizations

Provide nominal, real, per-capita, GDP/Crown-share, budget-versus-actual,
revision/vintage, classification, department/portfolio and pharmaceutical
budget analyses with coverage and quality summaries.

**Acceptance:** AC-07, AC-08, AC-10, AC-11.

### M-14 — Rights-aware Platinum metadata and federation

Generate schema-as-code, DCAT, Croissant, RO-Crate, PROV, cards and catalogue
projections with source-specific rights. Provide stable, versioned federation
keys for the reimbursement and medicines atlases without making their runtime
state authoritative.

**Acceptance:** AC-14.

### M-15 — Operable, resumable archive workflows

Expose typed CLI and read-only MCP surfaces plus bounded scheduled capture.
Support dry-run, idempotency, interruption, retry, resume, reconciliation and
structured failures without an always-on service.

**Acceptance:** AC-13, AC-16.

### M-16 — Recovery and reconstruction

Reconstruct Silver, Gold, SQLite, plots and Platinum metadata in a clean
environment from Bronze objects, manifests, locked code and parameters.

**Acceptance:** AC-08, AC-12, AC-16.

### M-17 — Gated Hugging Face publication and verification

Build a checksum-pinned, rights-eligible candidate for
`edithatogo/nz-health-appropriations`. Upload only after explicit approval and
credential availability; verify remote bytes, metadata, viewer/Parquet
behavior, immutable revision and collection membership before any publication
claim.

**Acceptance:** AC-14, AC-15.

### M-18 — Test, security and supply-chain assurance

Use red/green/refactor sequencing and deterministic, non-restricted fixtures.
Critical integrity, rights, versioning, recovery and publication logic require
100% line/branch coverage plus property and mutation testing; overall
production coverage remains at least 95%. Full repository, schema, type,
security, licence and SBOM gates must pass at checkpoints.

**Acceptance:** AC-16.

### M-19 — Traceable accountable state

Keep Conductor artifacts, a parent issue/subissue hierarchy when authorized,
run logs, machine/human evidence, commits, hosted state and external gates
cross-referenced without conflating local readiness with external completion.

**Acceptance:** AC-04, AC-15, AC-16.

## Should

### S-01 — Preservation packaging depth

Use WARC 1.1 for material HTTP context, an OCFL-compatible object layout and
BagIt-compatible bounded transfer/recovery packages.

### S-02 — Multi-hash and authenticity evidence

Record SHA-256 plus BLAKE3/CID where supported and produce checksum-pinned,
signable/timestampable manifests without requiring signing keys for local
validation.

### S-03 — Rich workbook inventory

Inventory formulas versus cached values, named ranges, tables, charts,
comments, merged/hidden cells, hidden sheets, external links, macros and
embedded objects without altering the original package.

### S-04 — Automated source health and drift reporting

Report source freshness, schema fingerprints, range/layout drift, missing
vintages, rights changes and cross-source reconciliation variance.

### S-05 — Aggregate health-outcome linkage

When justified by a specified question, link published aggregate Health
Survey indicators through stable time/geography definitions; never ingest
unit-record microdata under this track.

### S-06 — Portable metadata and citations

Provide machine and human citation exports, data dictionaries, changelogs and
consumer examples for DuckDB, Python and Hugging Face.

## Could

### C-01 — Rebuildable graph projection

Publish entity/relationship tables connecting appropriations, agencies,
classifications, sources, vintages and atlas identifiers.

### C-02 — Reproducible semantic search

Evaluate embeddings and Lance/LanceDB only with pinned models, source hashes,
quality/drift evidence and a demonstrated discovery use case.

### C-03 — Static analytical report

Generate a read-only static longitudinal report from Gold products without
introducing a bespoke interactive application.

### C-04 — Further directly relevant official series

Add audited health workforce, service-volume or aggregate outcome datasets
only through a scoped amendment that identifies the analytical join, rights,
classification compatibility and preservation burden.

## Won't

- **W-01:** Rewrite or merge donor Git history.
- **W-02:** Delete, archive, or make deprecation claims about the donor.
- **W-03:** Store large source payloads in Git.
- **W-04:** Publish restricted, personal, private or unpublished information.
- **W-05:** Acquire New Zealand Health Survey unit-record microdata.
- **W-06:** Make causal, policy-effect or forecasting claims from descriptive
  fiscal data.
- **W-07:** Make graph/vector state authoritative.
- **W-08:** Create a Zenodo deposition or DOI under this track.
- **W-09:** Require an always-on service or custom interactive frontend.

## Dependency decision requirement

`openpyxl` and Matplotlib are candidates, not approved dependencies. Before
either enters production or the lockfile, the implementation must record a
capability comparison, security/licence evidence, reproducibility risks,
maintenance cost, focused fixtures, a `tech-stack.md` amendment and the
accountable dependency-adoption decision.
