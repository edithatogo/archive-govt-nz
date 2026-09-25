# Stats NZ annual mean population export

The official Infoshare export for `DPE056AA`, *Estimated Resident Population by
Age and Sex (1991+) (Annual-Jun)*, was acquired with `Mean year ended`, `Total`,
and `Total All Ages` selected and status flags displayed. Infoshare documents
its direct export workflow on the [official export page](https://infoshare.stats.govt.nz/ExportDirect.aspx);
Stats NZ's [30 June 2026 population release](https://www.stats.govt.nz/information-releases/national-population-estimates-at-30-june-2026/)
is recorded as the related release context.

The 1,676-byte CSV has SHA-256
`a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9` and is
preserved at the matching path under the external
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256/`
store. A strict parser validates the exact title, selected measure and universe,
annual coverage, row uniqueness, flags and complete known footer. It emits
source-faithful facts with June 30 reference dates. The export has 36 rows,
one `..` unavailable token, and two `P` provisional statuses. These are retained
as source context; they are not copied into Git as source values.

This is a follow-up observation after the older, date-bounded context census and gap assessment; those historical receipts remain unchanged. This was a browser download, and HTTP headers or a WARC response receipt were
not retained. The evidence therefore establishes the stored bytes' fixity, CSV
profile and publisher footer, but does not claim transport-level capture proof.
The resource-specific rights decision, other historical export vintages, and
selection of this mean series as a denominator remain open. No per-capita or
other population-based Gold measure has been produced.
