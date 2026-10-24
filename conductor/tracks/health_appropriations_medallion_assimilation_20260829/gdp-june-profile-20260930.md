# Stats NZ GDP June 2026 successor Silver profile

This increment adds a strict Bronze-to-Silver extractor and typed source
operation for the separately captured June 2026-quarter GDP workbook. It does
not replace or append observations to the March 2026-quarter package.

The pinned source is census record `stats_nz_gdp-588a47c19c9dbc44`, SHA-256
`b6d2fe15b4656143f600abeb1849432f60d769570667eb90d07ddacd3498e22d`. The
capture receipt is pinned at
`28609dbc48f7a4b68ea14f277267c7af0e2eec9b274d0c369865d7d090a2b868`.
The workbook's exact selected range is `Table 1!C27:BK27`, reference
`SG03AB01GE00S900`, prefix `SNEQ`, 61 quarterly current-price expenditure
actuals from June 2011 through June 2026, in the literal unit `$(million)`.
The distinct seasonally adjusted Table 2 series is excluded. Currency remains
unverified; values are not annualized, currency-qualified or selected as a
denominator.

The profile records 61 facts, 915 field-lineage rows and 2,323 dispositions over
nonempty workbook cells. The extractor checks the release title/date, exact
sheet dimensions, merged ranges, selector labels, period row and number format.
Two clean local source-operation runs from the pinned Bronze object matched all
four package files:

| Product file | Bytes | SHA-256 |
| --- | ---: | --- |
| `MANIFEST.json` | 1,081 | `f54b0ad605b54e480cd0623360159b3ce14b6a9f762185d5244dec89837ffbfd` |
| `gdp_facts.parquet` | 29,409 | `ab95deb1701876f285b567da245bdabd842559c7ea9c64ebd2aca2740373d35a` |
| `field_lineage.parquet` | 17,815 | `ad698d41f4709b633df875d256c419107ebe044fd325b5afdc74f56e3113e6dc` |
| `cell_dispositions.parquet` | 37,848 | `22143c282b9e28cbfcae41c9531f1b37b710b6a5a5d5fbcf9fa6112e196b9dd9` |

The integrated clean-room receipt confirms the Bronze CAS tree remained
unchanged. Rights are `not_evaluated`, publication is `not_performed`, and
canonical projection remains `not_performed`. The 61-quarter source was not
added to the existing four-input Context Gold contract; any future canonical
projection or temporal comparison must preserve it as a separate vintage and
earn a distinct source-specific review.

The official copyright page's general CC BY 4.0 statement and exceptions were
observed in the capture receipt, but no legal or resource-specific rights
approval is asserted here.
