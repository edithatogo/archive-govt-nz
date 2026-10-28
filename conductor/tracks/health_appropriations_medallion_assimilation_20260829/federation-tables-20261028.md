# Evidence-supported federation tables — 2026-10-28

M-14 / AC-14, Phase 7.2. The user explicitly retained the ten reviewed exclusions
and zero approved positive links. This completes the typed table projection for
that pinned scope. Other source grains, future vintages and positive-link
admission remain unqualified; they are not inferred from successful table builds.

## Products

| Table | Native rows | Meaning |
| --- | ---: | --- |
| `source_records.parquet` | 5 | Exact source record identifiers, qualified package/profile/manifest pins and literal periods |
| `partner_records.parquet` | 174 | Selected reviewed partner identifiers, actual repository/table/key field, pinned revision/snapshot and record grain |
| `mapping_dispositions.parquet` | 10 | Reviewed annual Vote-total/partner-grain exclusions; target key, confidence and join interval stay null |
| `approved_links.parquet` | 0 | Typed empty relationship table; no positive links are approved |

`federation_tables.json` records physical Arrow schema descriptors, row counts,
byte/hash controls, exact readiness/review pins, and the retained publisher-control
warning. The selected historical medicines snapshot retains its one documented
README checksum mismatch; the independently approved hosted correction does not
rewrite that snapshot or retrospectively remove its observation.

Source and partner identity keys use the explicit local
`archive-govt-nz.health-federation-key/v1` scheme. Their content-addressed IDs bind
the original package/record or partner namespace/revision/table/key field/record.
Raw keys are retained. Local key construction is not a partner key-scheme
approval or semantic equivalence assertion. Source period tokens are preserved;
no fiscal dates, comparability, effective interval or confidence are invented.

There is no input for positive rows and no approval override. New approved links
would need compatible grains, explicit versioned keys, method/confidence/period
and lineage evidence, plus source-specific rights qualification. Existing
unmatched/ambiguous fixture contracts remain; no unseen records are fabricated
as pending, unmatched or ambiguous. Every current reviewed pair is excluded.

## Integration and verification

The existing qualified overview exporter/verifier accepts
`include_federation_tables=True` only with discovery and all pinned partner/review
snapshots. It first re-verifies source products, qualified resource evidence and
the immutable partner-review ledger, then emits v4 with the four tables and
inventory. Existing v1/v2/v3 defaults and their payloads remain unchanged. The v4
card retains the complete v3 card as a prefix. New tables receive no inherited
licence or release approval. This is local metadata production, not publication.

The pure table projector only describes supplied assertions; authority belongs
to the surrounding pinned source/snapshot reconstruction path. Read-only v4
verification reconstructs every expected byte, including Parquet. Rehashing a
forged positive-link table and its manifest cannot qualify it.

## Evidence and acceptance

Paired JSON records two native v4 builds using five qualified editions, four
retained partner/review snapshots, five source records, 174 selected partner
records and ten exclusions. Both complete outputs match; source/snapshot inputs
and the retained v3 installation are unchanged. DuckDB independently reads zero
approved rows and exactly ten excluded rows; disposition source keys resolve to
the source table. Focused tests cover replay/default stability, the forged-link
case, and rejection before writing when pinned review is absent. A fixture
missing identifiers was rejected; explicit fictional IDs/periods were added to
the fixture rather than weakening source-key admission.

JSON Schema covers the table inventory and v4 reconstruction receipt. The full
harness and protected delivery are recorded when terminal; the wider Phase 7
rights/metadata/review checkpoint remains open.
