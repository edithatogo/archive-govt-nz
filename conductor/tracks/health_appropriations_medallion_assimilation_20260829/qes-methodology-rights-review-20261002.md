# QES reference-period, composition, and rights review

This review links the retained June 2026 QES workbook profile for
`QEMQ.SASZ9A` to the official Stats NZ QES series and collection metadata. It
qualifies how to interpret its quarterly period labels and records the specific
limits that remain before annual analytical use.

## Exact selected measure

The retained source is the Stats NZ June 2026 QES workbook
(`1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97`). Its
Table 8 labels identify `QEMQ` at A8, Total at P6, Ordinary time at P7, and
`SASZ9A` at P8. The selected series is total-sector ordinary-time average
hourly earnings, reported in the workbook as `$` per paid hour, with nine
quarter observations from 2024Q2 through 2026Q2. This confirms the local
selector; it does not establish an ISO currency code.

## Period and method

Stats NZ DataInfo+ QES series metadata version 87 says observations refer to
the pay week ending on or immediately before the 20th of the middle month of
each quarter. Quarter labels were renamed in 2003 without changing that
reference week. Thus the quarterly observation is a middle-month reference-week
measure, not an average over all days or pay weeks in the quarter.

The selected observations post-date the March 2021 QES redesign, which moved
collection from geographic units to kind-of-activity units (KAUs), reallocates
sample strata each quarter, and uses administrative data for state-sector
schools. Sample rotation began in March 2023 and can increase sampling error in
quarterly and annual changes. QES uses employee-count weights from the Business
Register and imputes non-response. Its reported average earnings reflect
changes in the mix of businesses, industries, and occupations as well as
changes in earnings. Stats NZ distinguishes this from the Labour Cost Index,
which controls job characteristics to measure the cost of the same work.
Accordingly, QES ordinary-time hourly earnings are not a constant-quality
wage index.

The retained Table 8 workbook and existing profile identify ordinary-time
earnings divided by paid hours; Table 8 carries the `QEMQ` family and
`SASZ9A` selector alongside that measure label. A check of Stats NZ's June 2026
labour-market summary found an explicit footnote that average ordinary-time
hourly earnings are not seasonally adjusted. Together, the retained exact
selector and current official summary support `not_seasonally_adjusted` for
the selected indicator; they do not provide an ISO currency code. The series
remains unapproved for deflation, annual weighting, or joins to fiscal-year
spending.

The June 2026 summary is a contemporary measure-level statement; the retained
workbook supplies the selector-to-label mapping. Neither changes the retained
workbook bytes or original adapter receipt, and no live Infoshare response was
acquired for this follow-up. The correction is confined to the supplemental
definition: native currency remains unknown, rights remain unadjudicated, and
analytical selection remains unmade.

## Rights observation and unresolved qualification

The official DataInfo+ series metadata identifies Statistics New Zealand in
its Rights field and has an empty License field. Stats NZ's website copyright
statement says its content is generally licensed under CC BY 4.0 unless
otherwise specified and requires attribution. The retained workbook is a
Stats NZ-hosted official source, but its DataInfo+ item supplies no item-level
license identifier and the workbook's specific exceptions have not been
adjudicated here. The review therefore records the publisher-default
observation while keeping rights eligibility unadjudicated; this is not legal
approval or publication authority.

The exact HTTP response bytes are preserved in
`qes-series-metadata-20261002.json.gz` (gzip SHA-256
`a94492c389a058ac19c62e7e12604a801d37ea4cf7ea060d08927f6e0676c466`; decoded
SHA-256 `be2715d1549f68bf2b0e60a9262b204690f8dbf8105c4c565594ea09d566df3f`)
and `qes-data-collection-metadata-20261002.json.gz` (gzip SHA-256
`f2903a4134b17018b1ebd0e445de575067da50ff265b966924701f1ad000fedb`; decoded
SHA-256 `699a1fbb3df5b849974604b1a67dbbe0b1e15997921a3877699565c15151a19b`).
Readable JSON copies are also retained with LF line endings; the source review
pins both these normalized copies and their compressed raw responses. The
series metadata is version 87, last updated 2026-05-03; the collection metadata
is version 19, last updated 2021-04-27. Both are official Stats NZ DataInfo+
JSON exports retrieved 2026-10-02. Their own rights/license fields remain
exactly as supplied and are not rewritten.

Sources:

- [Quarterly Employment Survey, DataInfo+ series metadata](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/086258b1-90e6-4728-981d-756b3ca6e147/87)
- [QES Data Collection, DataInfo+](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/0394e202-f8c6-482c-89a3-49b16a20bf95/19)
- [Stats NZ copyright and attribution](https://www.stats.govt.nz/about-us/copyright/)
- [Labour market summary, June 2026 quarter](https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/Labour-market-statistics-June-2026-quarter/Download-data/labour-market-statistics-june-2026-quarter-summary-diagrams.pdf)
