# Metadata standards: explicit local mapping route

The initial primary-specification review produced no standards-shaped output.
The entity-only PROV helper is now implemented in `local_prov.py`; its receipt
remains descriptor-only. The verified local DCAT projection described below is
under implementation/review. Neither helper claims full standards conformance,
rights eligibility or publication. Version selection identifies documents
inspected, not a claim to use the newest release.

## Implemented bounded slice: PROV entities and derivation

PROV-O allows entity-to-entity derivation without requiring an invented activity
or actor. A scoped projection can map each verified original/product identity to
`prov:Entity`, and each product-to-input edge to `prov:wasDerivedFrom`. Keep the
direction product → input. Do not fabricate agents, execution times, generation
events or qualified provenance from a descriptor-only graph. This route follows
the [W3C PROV-O starting-point model](https://www.w3.org/TR/prov-o/#description-starting-point-terms).

The repository design should retain typed source/product namespaces, exact
package/payload pins, closed edge references and cycle guards. Compose the
existing typed descriptor validator or a separately tested strict inventory
reader; do not trust an arbitrary JSON object merely because it says `verified`.
Use an inline JSON-LD context with fully declared predicates so generation does
not fetch remote contexts. Test graph direction, dangling/colliding identities,
rights non-promotion, deterministic output and physical-schema retention.
Distinguish local structural/graph validation from full external conformance.

## DCAT: do not collapse rights categories

DCAT3 distinguishes licence, access-rights and other rights statements. Its
guidance uses separate Dublin Core predicates for these meanings.
[DCAT3 rights guidance](https://www.w3.org/TR/vocab-dcat-3/#license-rights)
supports keeping the local unresolved-rights state distinct from a licence.
Our mapping must not attach CC-BY, public access or an HF download URL merely
because metadata exists or original bytes were hash-verified. Exact physical
distribution metadata can be prepared locally; new public locations and rights
eligibility remain separately evidenced inputs.

### Verified local DCAT projection

`read_local_dcat(tuple[CanonicalPackageInput, ...])` in the health domain's
`local_dcat.py` composes the existing strict local reader. It verifies original
and raw-package hashes, canonical file closure, schema metadata, and equality
with recomputed canonical projections before returning any graph. Arbitrary
JSON claiming to be verified is not accepted. It retains the complete reader
receipt, exact row/byte/schema/payload metadata and derivation inventory beside
the graph, with deterministic hashes binding both outputs.

Each package-version recordset is one Dataset with one local Parquet
Distribution. Different tables and years are not silently modeled as alternate
representations of the same data; this follows the
[DCAT distribution distinction](https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution).
Dataset/distribution URNs use distinct namespaces and the validated product
identity digest; they identify snapshots, not a permanent cross-version concept.
Exact byte counts use explicit `xsd:nonNegativeInteger` literals, consistent with
[DCAT byte size](https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_byte_size).

Standards review replaced the draft's free-text format with the
[IANA Parquet media-type identifier](https://www.iana.org/assignments/media-types/application/vnd.apache.parquet),
using `dcat:mediaType` as recommended for registered types. Each Distribution
also exposes its already verified payload digest through `spdx:checksum`, an
explicit SHA256 algorithm IRI and an `xsd:hexBinary` value, following
[DCAT checksum semantics](https://www.w3.org/TR/vocab-dcat-3/#Class:Checksum).
This is the retained Parquet file's hash, not the source workbook, metadata
graph or package marker hash. Tests independently hash the fixture file bytes.

The context is inline and does not fetch remote definitions. The graph contains
no access/download URL, creator, publisher, licence, access-rights claim, release
date or conformance assertion. Local retention is not public availability, and
the graph does not establish rights to release its accompanying inventory.
The existing general Gold exporter is not reused here because its default
publisher, generated dates and fallback access locations do not satisfy this
evidence boundary. No global exporter behavior or dependency is changed.

Verification covers the read snapshots under the existing trusted-parent
contract, not later filesystem state. An independent RDFLib test lane now
expands generated DCAT and PROV JSON-LD under scoped external-resource denial.
It checks exact graph predicates/counts, resource/literal distinction, integer
byte sizes, binary SHA256 values against file bytes, and entity/derivation
edges. This is a development test, not a runtime claim made by either helper.
DCAT application-profile validation remains a separate gate. Croissant, RO-Crate,
cards, resource-specific rights decisions and federation are still outstanding.

## Croissant1.0: required publication-shaped inputs remain explicit

The reviewed specification requires dataset-level licence, URL, creator and
publication-date information, among other fields, and describes FileObjects and
field-to-resource references. Its field model supports repeated/nested values.
See [Croissant1.0](https://docs.mlcommons.org/croissant/docs/croissant-spec.html).
Do not fill missing publication values from source observation time or borrow
the older published dataset's licence for changed products. A draft may report
missing inputs without claiming conformance. Exact Arrow decimal precision,
scale, nullability and list types need explicit round-trip tests; do not silently
advertise monetary decimals as binary floats. A consumer-loading test is distinct
from validating the JSON document's shape.

## RO-Crate1.2: root metadata is not a fixity manifest

The inspected root specification requires dataset identity, name, description,
publication date and licence, and a metadata descriptor pointing to the root.
It expressly does not make the metadata document an exhaustive inventory.
See [RO-Crate1.2 root specification](https://www.researchobject.org/ro-crate/specification/1.2/root-data-entity.html).
Therefore retain the existing exact closure/hash manifests even after a crate
projection exists. An explicit local-package event must not be silently relabelled
as public release. Do not assert full crate conformance until the selected version,
mandatory input meanings, local resource layout and validation strategy are
reviewed. Descriptive unresolved-rights text must not be presented as permission.

## Delivery boundary

PROV's bounded entity graph and the verified local DCAT projection do not close
the metadata phase. Croissant/RO-Crate drafts and negative readiness tests can
proceed without publication, but missing mandatory evidence must stay visible.
New RDF/JSON-LD validator dependencies require the repository's normal adoption
review; none was found in the inspected project lockfile. No full AC-14 or AC-12
completion follows from this proposal or from a successful local JSON inventory.
