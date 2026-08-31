# Local PROV entity projection

Bounded design: compose the already-delivered typed ProductDescriptor validator
and local inventory. Return a new JSON-LD document containing only prov:Entity
nodes and product-to-input prov:wasDerivedFrom edges, the full unchanged inventory,
and a receipt binding both serialized documents to their SHA256 digests.

PROV-O supports entity-only derivation chains without an invented activity or
actor. See the [W3C starting-point model](https://www.w3.org/TR/prov-o/#description-starting-point-terms).
Inline context, absolute existing typed identifiers and canonical ordering avoid
remote context retrieval or caller-path disclosure. The complete inventory keeps
physical schema, package/payload pins and edge-kind information that the small
PROV graph does not encode. Declared dependencies remain assertions, not newly
observed derivation events or content fixity.

No I/O, automatic provenance discovery, new dependency, source mutation, licence,
execution timestamp, release date or publication. No full RDF/JSON-LD/PROV
conformance claim: tests validate this bounded structural and graph mapping,
not an external standards processor. This does not close AC-14 or AC-12.
Receipt digests bind deterministic JSON encoding, not RDF dataset canonicalization.

Use red-first tests for the exact graph, direction/closure, all inherited
descriptor guards, deterministic ordering/digests, full inventory retention,
fresh output objects and no invented provenance or rights. Run independent
review, critical coverage/mutation and native validation before hosted delivery.

Initial missing-module collection test failed with ModuleNotFoundError and exit
2 before production implementation. No input or output archive state was touched.

## Local assurance — 2026-08-31

71 combined projection/inventory tests passed in 2.51 seconds with 100% branch
coverage (115 statements, 16 branches; new projection 23 statements/2 branches).
All six generated cold mutants were killed, zero cache hits, 18 tests in 15.78
seconds. The mutation coverage warning is retained in the log; it is not the
critical-coverage evidence. Ruff and the scoped type check passed. Two independent
read-only reviews found no actionable issue in the declared scope.

- Source SHA256: `f7a26e0a12648cf0f02033e522bed57105e53a37749af8076bada5dd0a5266ec`.
- Tests SHA256: `ded711b1554a9efe5319cfd25e7052db03bd512fc70c23ac0e88c0f9011f79e9`.
- Critical log SHA256: `fc4e1f8d393d3fd357cdd6eceb962b7c24ea29cfb6c1c89af9598cbe1faa7d2c`.
- Cold report SHA256: `cd6d6e09c57b7e728127b84ec137e6649cdcde7a55918c9b063da63b73ac7c5c`.

Native and exact-head hosted validation remain pending at this checkpoint.
