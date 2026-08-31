# Bounded country preservation pilots

`tools/foi_country_pilot.py` consumes already retained Canadian federal ATI
**institutional monthly nil returns**, provider schema and CKAN dataset metadata.
It does not fetch URLs, activate a scheduler or publish any payload. Its exact
source binding is `ca-federal-atip`, dataset
`0797e893-751e-4695-8229-a5066e4fe43c`, resource
`5a1386a5-ba69-4725-8338-2f26004d7382`.

The input directory contains `ati-nil.csv`, `ati-schema.json` and
`source-metadata.json` (the original CKAN `package_show` response). The adapter
requires the explicit Open Government Licence Canada declaration, a public active
dataset, the exact resource URL/CSV format/advertised byte length and expected
provider schema. It rejects malformed and duplicate organisation/year/month rows
without dropping them. These checks bind supplied metadata; they do not authenticate
its network origin, establish privacy clearance or replace a trusted acquisition
receipt. Each input is limited to 8 MiB.

Preparation writes exact originals, a deterministic per-row metadata index and a
manifest into a new private directory (0700, files 0600). Verification requires an
independently retained manifest SHA-256, reproduces the index and manifest from
originals and rejects additional or changed package files. Restore copies the
original bytes into a separate new private directory and rebuilds the same
manifest. Existing output directories are never overwritten. Filesystem ownership
must be trusted; this is not a sandbox against a hostile local filesystem owner.

```sh
python tools/foi_country_pilot.py prepare --source ORIGINALS --output PACKAGE
python tools/foi_country_pilot.py verify --source PACKAGE --manifest-sha256 SHA256
python tools/foi_country_pilot.py restore --source PACKAGE --output RESTORED --manifest-sha256 SHA256
```

The callable interfaces are `prepare(source, output) -> manifest_sha256`,
`verify(package, manifest_sha256) -> manifest` and
`restore(package, output, manifest_sha256) -> manifest`. Callers must reserve and
fence execution separately. An offline capture can establish retained bytes; it
cannot earn public-publication credit.

Coverage units are institution/month rows, not requests or response documents.
`enumerated`, `captured` and `verified` describe every row in the selected original
CSV. `source_denominator` and `country_denominator` remain null and
`country_complete` remains false. The provider warns that not all institutions
publish to this dataset. A fully retained nil-return CSV is not a complete Canadian
FOI archive.

The separate US local research pilot preserves one Department of Justice FY2025
annual-report XML and its source/policy pages. Its index enumerates nonempty XML
text elements, with value hashes and numeric-lexical flags. The XML includes case
names, footnotes and other narrative text; its complete raw XML therefore needs
review beyond the proposed institutional/numeric publication group. Neither pilot
has been publicly uploaded or assigned an approved rights/privacy decision.

Population and output limits are explicit: 25,000 CSV rows, 8 MiB for each original
or generated file, an 8 MiB index and 40 MiB for the complete package before any
output is written. The three-file restore is at most 24 MiB. An executor can reserve
64 MiB for package plus restore; this does not include transient process memory or
the already-retained input files. Overflow fails without truncating the population.
