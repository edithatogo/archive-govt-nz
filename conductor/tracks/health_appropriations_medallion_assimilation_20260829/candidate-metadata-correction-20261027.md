# Candidate metadata correction and retained-publication review

The retained v4 manifest remains at SHA-256
`9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
A read-only review reverified all 94 payloads before and after two local
projection runs. Its seven Parquet schemas reveal 12 declared Croissant columns
that do not exist in the referenced Silver table. The retained publication,
manifest and collection evidence are preserved without mutation.

The active health candidate builder used that same generic descriptor route,
a fixed publication date, blanket README licensing and activity declarations
that the assembler did not verify. Future local builds now use actual Arrow
fields and exact IPC schema descriptors. Field IRIs are percent-encoded while
source column names remain literal. Existing Gold discovery and entity-only
DCAT/PROV projection code is reused; its verified Gold entry point is retained.

The local payload inventory binds relative paths, observed hashes and sizes.
Original-resource assertions must match the actual original-file hashes.
Parquet schemas are bounded and reject duplicate column names. Other payloads
remain opaque bytes rather than acquiring guessed semantic formats. The
assembler rechecks payload hashes before saving its final manifest.

The new local builder emits `partial_not_release_ready`, with original-resource
assertions distinguished from unqualified derivative rights and unrequalified
source-disposition assertions. Its card emits no blanket licence. Projections
invent no publication date, actor or activity, and report missing qualification
properties and custom Arrow-type loader limitations. The existing release
verifier rejects this incomplete inventory profile. A successful local build
therefore does not grant release readiness or publication approval.

`candidate-metadata-retained-review-20261027.json` records all input fixity,
seven observed schemas, the 12 legacy absent-column bindings and zero absent
bindings in the new projections. Both projection runs were byte-identical.
Their separate local sidecar files are retained under the external assurance
root; they are not installed over the historical candidate. Input-manifest pins
in these projections identify the generated payload-inventory manifest, not a
new release approval or the final whole-candidate manifest.

Full Croissant/RO-Crate conformance, ML loader qualification, resource-specific
rights decisions and approved federation remain separate open contracts. No
external publication, collection change or new rights adjudication was performed.

## Validation and final scope review

The 50 affected contracts passed, followed by the complete local harness:
8,458 tests, 14 capability skips, 96.89% measured coverage against the unchanged
80% gate, 81 schemas / 71 representative documents, parity 9/9 and all configured
mutation and supply-chain gates. The existing verified Gold entry point retains
its behavior; the unverified inventory projection is separately named and scoped.

A final review changed only the projection's payload-staging marker to
`outside_projection_scope`, avoiding an assertion about a caller's activity.
The two directly affected contracts passed again, and the retained-candidate
review repeated with all 94 source payloads unchanged. Every projection byte
except that report marker remained identical. Relevant static/evidence gates
are rerun for this clarification; exact final-head hosted assurance remains
separate from the preceding full local run.

Hosted review identified an original-destination compatibility boundary: a valid
128-character source identifier plus a suffix exceeded the inventory's generic
128-character component limit. The inventory now applies the existing bounded
original filename contract only to direct children of `original/`; all other
components retain the generic limit and traversal, reserved-name and collision
checks. The actual builder is exercised with both `.csv` and the maximum
10-character extension, preserving originals and repeat-build equivalence.
All 147 affected metadata, original-path and inventory contracts passed. Required
hosted assurance is repeated for the corrected commit; earlier successful local
full-harness stages are retained rather than rerun unnecessarily.
