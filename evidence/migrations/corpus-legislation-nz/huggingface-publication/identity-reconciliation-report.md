# Hugging Face identity reconciliation

Observed anonymously on 2026-09-01. No remote mutation was performed. Exact machine evidence is in `live-identity-observations.json` and `identity-reconciliation-report.json`.

| Identity | Exact revision | Role | Access | Listed files | Raw payloads | Parquet |
|---|---|---|---|---:|---:|---:|
| `edithatogo/corpus-legislation-nz` | `1efa35e72c378068cfb112d060bd0502497f61b1` | canonical | auto-gated | 112 | 95 | 7 |
| `edithatogo/corpus-legislation-nz-historical` | `ea9e66fb89c3230fc478f7c6f05f1a82f4fa1174` | superseded historical | open | 6,788 | 6,609 | 164 |
| `edithatogo/nz-legislation-corpus` | `1dea0c678b419a9c16fe7e363488f91d293391d3` | immutable DOI snapshot | auto-gated | 20 | 9 | 1 |

The roles are distinct, but all three live cards still identify `edithatogo/corpus-legislation-nz` on GitHub as origin. The canonical card therefore does not yet establish target-origin authority from `edithatogo/archive-govt-nz`. Donor lineage should remain explicit when that metadata is superseded.

The historical manifest records 6,609 records and raw payloads, 164 Parquet files, 6,775 controlled files, 5,712,316,655 bytes, and content root `bc6d1b1d5d308dc2797ad18126b272767c1a05cf1feee173c322adf4cdfeb8a9`. Its public viewer instead exposes `manifests/validation_report.json` as a single `validation` row. That viewer row is not a corpus row count.

Both gated identities list `RIGHTS.md` in exact-revision inventories. Anonymous file resolution returns HTTP 401. A readback must represent file presence separately from whether its bytes were anonymously or authentically verified; it must never translate access denial into `has_rights_statement: false`.

The historical card mixes a superseded/historical registry role with text calling it the live operational home. Its `raw_xml/` prefix also contains a README, explaining the apparent 6,610 prefix count versus 6,609 content files.

Canonical and DOI payload roots, record counts, and schemas remain unknown from anonymous access. Publication continuity remains externally blocked until an authorised canonical metadata/state revision is published and its exact returned revision is independently read back under the documented access contract.
