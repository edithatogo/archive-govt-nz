# Vote Health Supplementary Estimates financial activity — 2012/13

The official 33-page Treasury supporting-information PDF is pinned by source
SHA-256 `07aaafdc58bd448ce2ef60d3c2dce071dfc3204838b21d01cad105e7e0d946fc`.
Its capture manifest records the Treasury CC BY 4.0 notice and a matching WARC
response. The extractor is edition-specific and reads only page 2, the
“Summary of Financial Activity”.

The Silver package contains eleven explicitly named rows from the Appropriations
and Crown Revenue and Capital Receipts sections. It retains the five printed
`$000` columns, all 55 field-lineage entries, and raw dash/`N/A` tokens; those
tokens become null values and are never treated as zero. All remaining PDF pages
and rows remain preserved-only. Two clean-room builds and the retained package
match across the manifest and Parquet digests in
`vote-health-supplementary-2012-13-financial-activity-20261023.json`.

The capture record's licence notice is not a legal or resource-specific rights
approval. Fact rights remain `not_evaluated`; currency code, annual bounds,
cross-edition comparability, canonical/Gold admission and publication are not
qualified by this slice.
