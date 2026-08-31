# Verified source-derived Gold export

## Preservation and semantics

The shared raw reader verifies the pinned raw run, bounded manifest/Parquet
snapshots, canonical record identities and source/amount lineage before
returning unchanged canonical values. SQLite compatibility and Gold use this
same reader. The refactored compatibility rebuild matches all four previously
retained files byte for byte.

Gold consumes the 215 Budget and 106 historical facts. The 20 BEFU/HYEFU
summary facts remain in Silver and compatibility output; the Gold manifest
explicitly reports both excluded profiles and the analytical-scope reason.
No source is deleted or silently omitted from the archive.

The new exclusive directory contains five typed Parquet tables, exact input
records, all selected field lineage, and a completion manifest. Empty tables
retain their explicit schema. Source historical amounts remain Decimal(38,17);
Budget aggregate amounts use Decimal(38,3). Percentages are lossless decimal
strings with the recorded 12-decimal-place rounding policy. Source context,
formula policies, input IDs and unavailable-comparison reason codes are kept.

Default CLI behavior is preflight only. Existing, partial, symlink and
input-overlapping outputs are rejected. Failed new attempts retain partial
bytes and a redacted failure receipt; partial-export resume is not claimed.
No formula execution, publication, rights grant or original mutation occurs.

## Live local receipt

Retained directory: `gold/raw-analytics-20260831-v1`.
Raw-run manifest:
`da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
Gold manifest:
`ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`.

Four independent eight-file builds match, including a build after the provenance
review fix. Independent readback verifies every output hash,
the manifest schema and identity equality between all 321 selected facts and
4,798 lineage records. Original donor bytes are unchanged before/after
read-only SQL comparisons.

| Table | Rows |
| --- | ---: |
| historical_nominal | 53 |
| historical_yoy | 53 |
| health_spending_gdp_share | 53 |
| recent_classification_trends | 16 |
| recent_functional_breakdown | 4 |

All 16 legacy Budget aggregates and four breakdown values match exactly.
All 24 overlapping historical nominal values match after explicit legacy
binary conversion; GDP shares match under relative tolerance 1e-12 and
absolute tolerance 5e-12, not exact-decimal parity. The prior source-token
reconciliation still applies. Gold additionally retains 29 source-only years.

Of the 24 legacy growth rows, 21 comparable calculations match with that
explicit float tolerance. The initial observation is 1972. The legacy 2020
growth calculation compared with 2000; the restored source series correctly
compares with 2019. Growth at 1997 is now unavailable under the accounting-basis
change guard. These are disclosed semantic differences,
not reasons to change original data or silently fill missing growth with zero.

## Validation and operation

The initial 42 focused tests passed at 100% critical line/branch coverage across
the shared reader, compatibility exporter and Gold exporter. All initial 79
unfiltered mutants were killed without pardons; report
`74739185d4706f7997432917287d146c507db191c9ad1b623d8bb061008e5821`.
The provenance review adds four fail-closed cases for source fields colliding
with the reserved `input_profile` annotation: all 46 focused tests pass at
100% critical coverage. Such inputs are rejected, not silently overwritten.
Full local assurance remains unsuccessful because of recorded timing failures
and stage timeouts in the original Gold attempts. Independent hosted assurance
subsequently passed all seven checks at head
`3895434eea49dec019ae48bdcdf70626ae1b1c71`; PR #261 merged as
`15b47b946a27a47efd4715002f0c1aff563149d4` at 2026-08-31T04:50:48Z.
Health source/tests were unchanged at merge; whole trees differ because of
intervening main work. Hosted success does not retroactively pass local failures.
The final post-fix mutation attempt records 63 kills, 16 timeouts, zero survivors
and zero pardons, report
`63eb5293fdbabfb980c7fb0551094a9ba3808110099c41f217cd207a68b4da65`.
Timeouts are not counted as verified kills. Current-main schema validation
passes 37 schemas/27 documents; Conductor validates 69 tracks.
See the run log for exact attempts, diagnosis and subsequent receipts.

```sh
uv run --locked archive-govt-nz health-appropriations-export-gold \
  --raw-run /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver/raw-orchestrated-20260830-v1 \
  --store-root /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas \
  --manifest-sha256 da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269 \
  --output-dir /path/to/new/gold-directory
```

Add `--no-dry-run` only for a new local output directory. This does not approve
an HF candidate. Next: six source-derived plot semantic contracts and
deterministic rendering, retaining all donor PNGs in Bronze unchanged.
