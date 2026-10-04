# Local analytical Gold metadata — 5 October 2026

The Fiscal analytical and Budget comparison Gold profiles now produce a separate
six-file local metadata package: catalogue.json, schemas.json, dcat.jsonld,
prov.jsonld, DATASET_CARD.md and MANIFEST.json. This completes the bounded
M-14 / AC-14 follow-up for these two supported profiles, not all Platinum.

Existing typed Gold readers verify inputs before metadata generation. Inventory
snapshots independently bind every payload and Gold manifest to its SHA-256 and
size. Source originals, source meaning and rights are not reassessed by this
operation. Metadata preserves exact Arrow IPC schema bytes, field types and
nullability, per-recordset row and state counts, and observed period-end extrema
and distinct counts. Extrema do not claim continuous temporal coverage. No data
rows or absolute local filesystem paths are emitted.

DCAT describes each Parquet recordset as a separate dataset/distribution with
registered media type, typed byte size and SPDX SHA-256 checksum. PROV represents
Gold package membership and metadata derivation from those exact local packages;
it does not invent source verification, activities, people or generation times.
Inline contexts parse with the existing RDF processor under denied external
file/network access. This is bounded vocabulary/projection validation, not full
DCAT application-profile or standards conformance. References:
[DCAT 3](https://www.w3.org/TR/vocab-dcat-3/) and
[PROV-O](https://www.w3.org/TR/prov-o/).

Cards retain product caveats and local content-addressed citation identifiers.
Rights remain not_evaluated; publication is not_performed; release readiness is
blocked_unassessed_rights_and_publication. Unsupported or missing rights states
are rejected even after repinning a manifest. No licence, publisher, public
access URL, DOI, author or federation link is inferred. Broader Croissant,
RO-Crate, rights application profiles and approved federation remain open.

The CLI health-appropriations-build-gold-metadata accepts explicit Fiscal and
Budget package paths and manifest pins, an output directory and optional --write.
Dry run performs verification without writes. Writes require a new directory,
reject bidirectional input overlap, preserve interruptions and return an immediate
metadata reconstruction receipt. Exclusive-write failure emits a bounded failure
receipt and exit 2. The library verifier rechecks Gold inputs and compares every
metadata byte with a freshly rebuilt projection; metadata pins alone are not
source verification or release approval.

Three focused tests cover typed admission, repeat builds, actual installed CLI
process completion, corruption, incompatible/missing rights and offline RDF
inventory/derivation. Target remains 80%. Native builds consume retained qualified
Gold snapshots; they do not redo Bronze normalization. Two builds match all six
files, describe 384 rows across five recordsets, independently verify inventory,
schemas, state counts and observed periods, reject bad pins, return exit 2 on
exclusive write, and leave Gold inputs unchanged. The paired Budget inputs come
from the preceding byte-identical native Gold replay. The Fiscal input is the
retained qualified analytical package; it is consumed unchanged by both builds.

Machine evidence is in gold-metadata-20261005.json. Raw Gold tables and generated
metadata remain outside Git. Full harness and scoped phase review follow; this
scope does not close final Health recovery/review gates.

Final required ./scripts/validate.sh passed: 7,472 tests / 10 skips, 97.90% aggregate coverage with the unchanged 80% floor. Format, lint, strict typing, schemas, parity, configured mutation and supply-chain gates passed. Scoped phase review passed; native paired six-file metadata replay and input preservation passed. Broader Platinum and final Health gates remain open.
