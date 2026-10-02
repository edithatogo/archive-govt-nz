# CPI index-reference qualification — 2026-10-02

The exact retained Stats NZ series is `CPIQ.SE9A`, selected as CPI All Groups
for New Zealand. Stats NZ DataInfo+ states that CPI indexes use the June 2017
quarter as the index reference period, with value 1000, except indexes added
in later reviews. The official [Index reference period concept](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/df1b7aa5-61d5-4d88-b485-1c2935ddc5a1)
states that this is the benchmark for comparing index levels. Stats NZ's
[CPI Data Collection 2017](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/74a24330-0516-4ae7-a65e-77b6ca3136ca)
also records the 2017-quarter base for CPI indexes, subject to later additions.

The retained June-2026 source object is pinned in `source-census.json` at
SHA-256 `f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d`.
Its selected `CPIQ.SE9A` observation for `2017.06` is `1000`, matching the
official reference period. This reconciles the series identity, published
definition, and retained observation without inferring the base from an
arbitrary value elsewhere in the series.

The CPI base is therefore recorded as June 2017 quarter (`2017Q2`) = 1000.
This resolves only `index_base_not_verified`. The census remains analytically
unqualified: no fiscal-year average/rebase policy or CPI-as-health-input-cost
interpretation is selected. The base qualification does not approve an
inflation-adjusted Gold measure or publication.
