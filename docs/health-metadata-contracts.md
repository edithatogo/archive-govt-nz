# Health metadata application contracts

The versioned candidate-v2 profile binds observed Parquet schemas and exact local
payload bytes to an operator-selected, separately pinned metadata/resource record.
Publication facts are explicit source assertions; build time, package creation,
licence inference and prior publication approval never supply missing facts.

The resource record covers every member, including generated metadata and the
candidate manifest itself. It remains outside the candidate to avoid self-hash
cycles. Legal accuracy and publication approval remain external decisions.

The existing inventory profiles and historical products retain their identities.
A successful inventory reconstruction cannot stand in for the release profile.
The qualified metadata report describes metadata and resource-assertion validation
only; the candidate verifier separately enforces closure, source dispositions,
revision pins, parity, recovery and assurance freshness. None performs publication.

## Standards profile and offline processing

The local profile uses Croissant 1.0, RO-Crate 1.1, DCAT 3 and entity-only PROV-O.
Its exact generated documents are reconstructed from observed inputs and explicit
facts. Croissant FileObject content references resolve to included local members;
they do not assert a hosted download endpoint. Field sources retain exact column
names and Arrow physical types. Explicit primitive Arrow-to-Croissant representation descriptors retain the
physical type separately and never cast payload values. Unsupported physical
types retain their custom identifier and block profile readiness; ML loading
requires separate proof. RO-Crate uses an embedded context subset, flattened contextual
entities, relative member identifiers and resource-scoped rights.

Administrative generated metadata is covered by the manifest and detached rights
record, without circularly hashing itself into the source-payload inventory.
Citations refer to included members; snapshot changelogs do not claim changes
against a previous release; local drill-through references do not invent upstream
source locators. Broader source citations and publication profiles need their
own source-backed evidence. Full universal conformance and ML loading are not
asserted by the local application contract.

References:

- [Croissant 1.0](https://docs.mlcommons.org/croissant/docs/croissant-spec.html)
- [RO-Crate 1.1 embedded contexts](https://www.researchobject.org/ro-crate/specification/1.1/appendix/jsonld.html)
- [RO-Crate 1.1 data entities](https://www.researchobject.org/ro-crate/specification/1.1/data-entities.html)
- [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/)
- [PROV-O](https://www.w3.org/TR/prov-o/)

## Application vocabulary

<a id="rightsState"></a>
### rightsState

An RDF property recording the supplied per-member state: `eligible_asserted`,
`unresolved`, `restricted` or `incompatible`. It does not establish legal truth
or authorize redistribution. Only resource assertions with matching payload and
evidence pins may supply a licence or attribution in this profile. Missing or
incompatible decisions block readiness; a dataset-wide grant is never inferred.

<a id="arrowType"></a>
### arrowType

The exact observed Arrow physical-type string for a field. It is descriptive
metadata, not an instruction to cast values or a semantic equivalence mapping.

<a id="nullable"></a>
### nullable

The observed Arrow field's nullability flag, without inferring completeness of
actual observations or interpreting a null as a monetary zero.

<a id="arrowSchemaSha256"></a>
### arrowSchemaSha256

SHA-256 of the observed Arrow IPC schema serialization, compared with the exact
serialized bytes represented by `arrowSchemaIpcHex`.

<a id="arrowSchemaIpcHex"></a>
### arrowSchemaIpcHex

Hexadecimal encoding of the exact observed Arrow IPC schema. Arrow type reference
identifiers retain their existing content-addressed naming rule; no ML-loader
conversion is asserted.
