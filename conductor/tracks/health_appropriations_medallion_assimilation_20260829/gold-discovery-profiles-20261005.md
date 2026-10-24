# Local Gold discovery candidates — 5 October 2026

M-14 / AC-14 now includes a separately pinned four-file local candidate package:
croissant.json, ro-crate-metadata.json, profile-validation.json and MANIFEST.json.
The existing six-file Gold metadata contract remains unchanged. These are local
inventory candidates, not conforming published datasets or a staged data crate.

Typed Gold readers qualify both supported products before generation. All ten
Gold files, including manifests, have exact SHA-256, byte size, media type and
content-addressed identifiers. Five recordsets describe every column with exact
Arrow type identifiers, nullability, field extraction references, full serialized
IPC schemas and schema hashes. Custom Arrow type IRIs are descriptive extensions;
no Decimal-to-float cast, array flattening or tested ML-loader interpretation is
asserted. Payloads remain in independently pinned Gold packages. No source rows,
absolute paths or invented download URLs are included.

The validation contract recomputes the candidates from verified Gold snapshots
and rejects altered inventory, field mappings, type identities or added licence,
publication/conformance claims. The readback verifier requires exact inventory,
bounded pinned snapshots, no symlink members and byte-for-byte reconstruction.
Dry run writes nothing; writes require a new directory and reject input overlap.
Interrupted products are retained. The new command
health-appropriations-build-gold-discovery-candidates accepts explicit Fiscal and
Budget package paths/pins, output directory and optional --write. Successful writes
return a reconstruction receipt; exclusive failure returns bounded JSON and exit 2.

The official specifications expose real missing properties. Croissant 1.0 requires
licence, creator, publication date, dataset URL and a conformance declaration;
these are withheld, as are all ten FileObject content URLs. RO-Crate 1.1 requires
publication metadata; the candidate lacks datePublished and licence, and withholds
the descriptor conformance assertion. The report records these gaps explicitly:
full conformance is not asserted and release readiness is blocked. Generic release
helpers that add a current date or default licence are not used.
References: [Croissant 1.0](https://docs.mlcommons.org/croissant/docs/croissant-spec.html)
and [RO-Crate 1.1 root requirements](https://www.researchobject.org/ro-crate/specification/1.1/root-data-entity.html).

Two focused tests begin red on the missing module, then cover deterministic builds,
installed CLI dry-run/write/failure, altered claims and pins, and exact offline RDF
file/recordset/field identity. Static checks and typing pass. The coverage floor
remains 80%; no additional tests are added solely to increase coverage.

Two native builds consume retained qualified Gold, not freshly normalized Bronze.
All four candidate files match byte-for-byte. Independent reads verify every file
and every Arrow column, schema hash and extraction reference. Actual candidate
RDF graphs parse with external file/network access denied. Gold inputs remain
unchanged. This does not close standards conformance, source rights, metadata
clean-room recovery, federation or the final Health assurance gate.

Native hashes and graph counts are in gold-discovery-profiles-20261005.json.
Raw Gold payloads and generated candidates are retained outside Git. Full harness
and scoped phase review follow.

Self-review found returned contexts aliasing the internal profile dictionary. Added a regression assertion to an existing test: red showed altered context accepted. Copying each context makes that assertion green and preserves every candidate byte. Two native v2 builds after the fix exit successfully and match v1 exactly. Required harness and scoped review are repeated for the corrected code; no gate was weakened.

Final required harness passed: 7,474 tests / 10 skips, 97.87% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates passed. The added assertion initially exceeded the test-function size limit; that failure was retained and the assertion moved into the existing RDF test. Corrected-code scoped phase review passed. Native v2 candidates remain byte-identical across both builds; broader standards, release, recovery and full Health completion remain open.

Hosted CI blocker: Linux passed the complete assurance harness twice, then Codecov CLI downloads failed with a TLS handshake error and missing signature files. The same host fails locally. The workflow now downloads the official GitHub v11.3.1 Linux release, verifies its pinned SHA-256 (independently matched against the release API and downloaded bytes) before execution, then uses the documented pre-downloaded binary input. OIDC, fail-on-upload-error and the 80% coverage floor remain enabled. Action lint and all six existing workflow-policy tests pass. Retained both hosted failures outside Git. See [Codecov action inputs](https://github.com/codecov/codecov-action) and [official CLI release](https://github.com/codecov/codecov-cli/releases/tag/v11.3.1).
