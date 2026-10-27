# Five Vote Health headline rights qualifications

This bounded M-04/M-14/M-17 and AC-04/AC-14 slice qualifies the extracted
page-2 headline data and source labels for 2022/23–2026/27. It does not close
Phase 7 or the track, approve federation, qualify other sources or authorise
publication. The existing historical candidate and every original stay unchanged.

## Official evidence and exception checks

Each individual chapter and its containing Health Sector volume explicitly
identifies Crown copyright under CC BY 4.0. Their exact URLs, source hashes,
attribution, scope and exclusions are in the versioned assessment ledger
`src/archive_govt_nz/domains/health_appropriations/overview_rights_20261027.json`.
The Treasury general policy is https://www.treasury.govt.nz/copyright-and-licensing .
The complete legal code was retained from
https://creativecommons.org/licenses/by/4.0/legalcode.en .

Twelve retained evidence files bind ten resource/collection field observations,
the Treasury policy observation and the original CC legal-code HTML bytes.
Treasury observations record rendered-page fields retrieved through `web.open`;
they explicitly do not claim original HTTP-body capture. The direct policy HTML
request returned 403. This does not erase the independently observed, explicit
edition and collection copyright fields. The ledger pins each observation's
exact bytes; the verifier rejects absent, extra or changed evidence.

All 339 PDF pages received a text-marker scan. The matched licensing/third-party
terms concern radiation licences or support services, not copyright notices.
The five selected page-2 images were rendered from hash-verified retained PDFs
and visually checked: the headline has no conflicting notice or third-party
credit. Each chapter's publisher record links to its retained PDF URL. Both
chapter and collection records carry the same CC BY 4.0 designation; no conflicting
exception was found for this selected material. Superseded publication status is
retained as historical-edition context and is not treated as licence withdrawal.

Qualification excludes original PDF redistribution, logos/emblems/trademarks,
images/design, unreviewed pages and unrelated source families. The data carries
Crown/source credit, an exact edition link, licence link, a change notice and a
non-endorsement statement. Code remains Apache-2.0. Source equivalence, currency,
comparability and analytical meaning are not altered by the rights decision.

## Implementation and reproducibility

`overview_rights.qualify_overview_package(request, silver_manifest_sha256,
evidence_root, fresh_output)` re-extracts and verifies the existing Silver via
the source-faithful Gold query, binds the exact source URL/hash/profile/vintage
to one reviewed decision, and verifies every supplied evidence pin. It creates
a fresh Gold manifest, unchanged facts Parquet, qualified query JSON, rights
record and attribution text. The two data resources have their own payload and
rights-evidence pins. Release readiness remains unassessed and publication is
not performed. Default Gold queries retain their existing unqualified contract.

The private evidence and fresh builds are retained under
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/assurance/rights-qualified-20261027/`.
The checked-in qualification receipt contains hashes and counts, not source PDFs
or rendered images. All five Silver file inventories equal their pre-qualification
recovery pins, all original hashes remain equal, and each qualified package was
built twice with every byte identical. No old manifest was rewritten.

The focused test initially failed at the missing module, then passed after
implementation. Contract tests exercise source-context mismatch, scope rejection,
output reuse/overlap and changed evidence, as well as repeatability, attribution,
per-resource fixity and unchanged source data. Full repository and exact-head
hosted validation are recorded separately during delivery.

Final scope review assigned a distinct schema version to the qualified query,
preserving the original unqualified API contract. The second native delivery
reused unchanged verified Silver and again built ten qualified outputs identically
in pairs. Their per-resource assertions pass the existing rights-assertions v1
JSON Schema. A wheel build independently confirmed that the assessment ledger
is packaged with byte-identical contents. The first complete harness attempt
stopped at the test statement-count lint limit; fixture refactoring resolved it,
and lint plus all remaining harness stages are run with the existing passing
lock, Conductor and format evidence retained.

Review clarification: the preserved source rows carry their original
`rights_state=not_evaluated` normalization observation. Both the new manifest
and qualified query explicitly identify `rights.json` as the effective scoped
assessment and preserve the source-row field unchanged. This is an additive
rights overlay, not a rewrite of historical provenance.

The complete official web-tool retrieval response for the policy and all ten
edition/collection pages is additionally retained as `official-web-retrieval.json`
(SHA256 `365e138238f2f6dfe43584c15a444f3bfd5f691601d8e7e0d53382e3af088ba2`).
This preserves the retrieved page content behind the compact observation records,
with its retrieval format explicit; it is not represented as original HTTP HTML.

## Local assurance checkpoint

Repo-local CPython 3.15.1: the complete test stage passed 8,461 tests with
14 capability skips and 96.89% coverage against the unchanged 80% gate.
The final rights-overlay clarification and bounded evidence enumeration passed
the two directly affected contracts; the source-faithful query contract also
passed. Relevant final format/lint/type/Conductor checks passed. The remaining
harness stages passed: 81 schemas / 71 representative documents, parity 9/9,
all configured mutation lanes, hygiene, dependency audit, licence inventory,
secret scan and the validated 118-component SBOM. No full test rerun was needed
for the metadata-only clarification; exact final-head hosted assurance remains
separate, including integration with the subsequently advanced main branch.
