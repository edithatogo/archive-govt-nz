## Qualified headline metadata — 2026-10-27

Integrated the five qualified 2022/23–2026/27 rights records into DCAT,
Croissant, RO-Crate and entity-only PROV metadata. Ten verified facts/query
resources carry the exact licence, attribution and scoped rights decision.
Original PDFs, source evidence, package collections and dataset roots receive
no blanket licence grant. Physical schemas and source/Silver/facts derivations
remain explicit; source-row normalization-time rights assertions are preserved.

The reader reconstructs qualified packages from pinned Bronze, Silver, ledger
and licence evidence before projection. A rehashed forged licence is rejected
before output creation. An initial focused regression caught an unintended
Dataset licence; the final projection licenses only the two data resources per
edition. DCAT rights links are typed resources and logical datasets have IDs
separate from physical files. Reused existing metadata projections; no parallel
metadata framework or external publication was introduced.

Native five-edition projection parsed all four JSON-LD graphs offline, finding
exactly ten licensed resources in each. Two complete exports were byte-identical;
Bronze, Silver, Gold and retained rights evidence were unchanged. The paired
JSON receipt records output hashes and graph counts. Products remain local
inventory candidates: payloads are referenced in verified external packages,
not copied into a distributable crate. Full profile conformance, publication
and unsupported federation relationships are not asserted. Wider Phase 7 and
track completion remain open. Focused rights/metadata contracts passed four
tests; complete milestone validation and hosted assurance are recorded separately.

Standards reviewed: [DCAT distribution licence](https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_license),
[Croissant](https://docs.mlcommons.org/croissant/docs/croissant-spec.html),
[RO-Crate 1.1 data entities](https://www.researchobject.org/ro-crate/specification/1.1/data-entities.html),
and [PROV entities](https://www.w3.org/TR/prov-o/#Entity).

Milestone validation passed on repo-local CPython 3.15.1: 8,549 tests passed,
14 skipped, 96.78% branch-aware coverage against the 80% floor; 83 schemas and
73 representative documents; parity 9/9. All configured mutation, dependency,
licence and secret gates passed; the SBOM validated with 118 components.
The initial harness stopped at test-import lint before running tests; its
correction preceded the one complete successful run. A subsequent evidence-only
receipt update reuses that unchanged implementation evidence.
