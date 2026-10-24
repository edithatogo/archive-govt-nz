# Vote Health Supplementary Estimates 2018/19 category totals

Added a hash-pinned Silver profile for the seven source-labelled category
totals on printed pages 386–390 (PDF pages 2–6) of Treasury's 2018/19
Supplementary Estimates. It retains the three printed columns separately:
Estimates Budget, Supplementary Estimates Budget, and Total Budget, in `$000`.
Source dash tokens remain null, parenthesized values remain negative, and each
field links to its source page and category row.

The exact Bronze SHA-256 is
`fc1cb3f5bc39d5ff7cd2805feaefd3ab1e2c0a3b2157249fb8de9084befce069`.
Two independent builds produced identical outputs:

| Output | SHA-256 |
| --- | --- |
| `vote_health_category_total_facts.parquet` | `f781644340258776a7b7d0bfab9e3ed924af96ec399c942c86c7c25fd76dec36` |
| `field_lineage.parquet` | `0ce2ff9c6a608bab184bf8efb80e88a0fa01a4b5f3c5288ab2bf15cc4d3dca51` |
| `page_dispositions.parquet` | `6c63e686f7fde476063b2ba2a865731ef701959bb02b7692d7fbd652c62fd918` |

The profile covers only these seven labelled totals, not the full appropriation
tables or PDF. Rights remain `not_evaluated`; no cross-edition join, currency
interpretation, source replacement, or publication is asserted. Focused parser
and dispatch tests passed before the full repository validation.
