# Metadata standards: explicit local mapping route

Primary-specification review only. No standards-shaped output, validator result,
new dependency, candidate or publication was produced by this review. Version
selection below identifies documents inspected, not a claim to use the newest
release. Existing local metadata remains a separately named inventory.

## Implementable next slice: PROV entities and derivation

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

PROV's bounded entity graph is a useful next implementation after the current
verified local reader. Croissant/RO-Crate drafts and negative readiness tests can
proceed without publication, but missing mandatory evidence must stay visible.
New RDF/JSON-LD validator dependencies require the repository's normal adoption
review; none was found in the inspected project lockfile. No full AC-14 or AC-12
completion follows from this proposal or from a successful local JSON inventory.
