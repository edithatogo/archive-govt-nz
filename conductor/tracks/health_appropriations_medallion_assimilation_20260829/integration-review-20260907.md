# Ordered health and FOI integration

The locked full repository harness passed on implementation commit
`e363eaffdc4d9e64bad32cf4b0093b73b9ca0b3f`: 5,363 tests, schema/parity,
all configured mutation suites, dependency audit, licence inventory,
credential scan and validated SBOM (112 components). CAS throughput was
670.31 MB/s. This receipt does not establish hosted delivery or clear rights.

Independent review found a generated-column schema bypass in the new donor
oracle. A red regression reproduced the acceptance of a virtual generated
column. Fix `82d8ba93b7b498ebb4aa9926248f02be43bcf978` uses `table_xinfo`
and requires the ordinary-column hidden flag. All 22 oracle tests pass;
independent re-review confirms rejection before the row query. The recorded
real donor replay is unchanged. Integration must rerun the full gate with
this fix before delivery.

The parallel FOI review found per-redirect crawl-delay enforcement, successful
page/terminal transport binding, and finite timeout-validation gaps. These
remain delivery blockers until fixed and re-reviewed. Prior observations are
historical evidence, not a claim that every collector policy was met.

Health and FOI tracks remain active. No publication, semantic repair approval,
schedule activation or terminal track acceptance is asserted here.

## Previously delivered local metadata clauses

Independent reviewer Banach compared the nine relevant source/test files with
both merged trees `4b1764bb` (PR #414) and `7afaec8e` (PR #415), verified their
successful hosted checks, and ran 188 focused tests successfully (six RDFLib
deprecation warnings). The five narrow Phase 7 clauses for guarded parser
loading, offline DCAT/PROV interpretation, Parquet/SPDX identities, verified
local DCAT generation and local provenance verification are accepted.
Croissant/RO-Crate application profiles, complete rights statements, cards,
federation ambiguity accounting and broader Phase 7 assurance remain open.

## Corrected integrated gate

All identified donor, population and FOI review defects were corrected and
independently re-reviewed. The probe runtime compatibility guard was additionally
inspected by the parent; its conservative rejection occurs before page access.
The locked full harness passed at `8b878a18`: 5,523 tests, 97.608983% coverage,
all configured mutation/supply-chain gates and validated SBOM. Exact evidence is
`ordered-integration-validation-20260907.json`. Hosted delivery remains pending.
