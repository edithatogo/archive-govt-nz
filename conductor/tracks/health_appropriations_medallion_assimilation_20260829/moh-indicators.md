# Ministry HAIR2024 published indicators — bounded profiles

## Source and semantic contract

The two retained UTF-8-BOM CSVs each contain exactly three columns and twenty
data rows, fiscal labels `2005/06` through `2024/25`. Figure27 labels the two
values as total appropriations excluding capital, COVID-19 and DSS, real and
nominal. Figure28 labels corresponding real/nominal per-capita indicators.
The complete exact headers are bound in `moh_indicators.PROFILES`; profiles
`fig27/v1` and `fig28/v1` require vintage `MoH-HAIR-2024`. Header spelling,
column order, period coverage and unique periods are mandatory. Input row
order is preserved rather than silently sorted. This is not a generic CSV
parser or automatic vintage detector.

Neither original specifies currency/scale, real-price base, deflator method,
denominator method or exact fiscal-year dates. The existing capture manifest
supplies source locators, attribution, fixity and rights records, not these
analytical definitions. No retained supporting report was identified in the
scoped source census. These gaps are not filled by inferring from matching
initial values, dividing rounded series or borrowing another source's basis.

Each source row yields two typed `published_indicator_fact` rows, deliberately
distinct from `health_spending_fact` and independently calculated Gold results.
Exact Decimal(38,18) amounts, original numeric tokens, fiscal labels, source
headers, nominal/real labels and explicit per-capita boolean survive. Unit,
price base, denominator and precise start/end dates remain null with structured
quality flags. These flags record unverified methodology, not a claim that
every missing method applies to every indicator. No inflation or population
calculation occurs. `rights_state=not_evaluated` does not override the separate
capture rights record or approve publication.

## Archival behavior

The adapter uses a capped, hash-verified snapshot (64KiB source, 2,048-character
line, 512-character field), strict UTF-8/BOM decoding and one physical CSV line
per record. Nonfinite/exponent/whitespace/missing numeric tokens are refused;
no unknown missing token becomes zero. Every fact carries all three original
field values and lineage; each input row has a disposition naming both facts.
Original quoting/BOM/newlines remain in Bronze. IDs include profile, source
hash, source row and field; observation context is preserved independently.

Default behavior is dry-run, writing nothing. Explicit writes require a new
exclusive directory; source/output symlinks and existing output directories
are refused. Interrupted writes retain partial files and no completion
manifest. No original, earlier derivative, network source or HF dataset is
modified. The existing fixed four-workbook orchestration is unchanged.

## Local pilots

Sources were hashed before and after two independently invoked builds each:

| Profile | Source SHA-256 | Retained manifest SHA-256 |
| --- | --- | --- |
| fig27/v1 | `c1e7758667b8255e049603de8325d732f34a76e6099e0fe4de6553a36d48e9fc` | `b3a9afc2bab6562373b73d2f5c45b76a244792acbf813bfb54b4e2b66bce76a2` |
| fig28/v1 | `7b9a51643550e3d890f4f341f27346d3466708fe924702ade4a731d1bb6266e4` | `714a0dd3fb53fa2ff26100e760983b791e81162fa30fb48d9f1d7131d8e338ed` |

Retained directories: `silver/raw-moh-fig27-20260831-v1` and
`silver/raw-moh-fig28-20260831-v1`. Each has40facts,120lineage entries and20row
dispositions. Both builds agree byte-for-byte for all four files. An independent
direct-CSV reconciliation checked all80amounts/raw tokens,240field mappings
and40row dispositions, plus all derivative hashes and unchanged originals.
This verifies extraction consistency, not the omitted analytical methodology.

## Validation and bounded failures

- Initial synthetic tests failed on missing module before implementation.
- An initial twenty-line preview omitted the final2024/25 row; the first live
  pilot correctly rejected the mistaken19-row contract before creating any
  outputs. Two corrected twenty-row synthetic tests failed first, then the
  explicit period contract was corrected. Both originals have20data rows.
- Initial partial-write test expected one retained file; the exclusive writer
  correctly retained the second empty file too. The test now asserts both
  retained files, zero-length interrupted file and absent final manifest.
-43focused tests cover exact profiles, byte-identical replay, full lineage and
  hash closure, strict numeric bounds, reordered periods, structural drift,
  byte/line/field exact boundaries, symlinks, context and interrupted writes.
  A bounded pure Decimal property retains its ordinary Hypothesis deadline.
- One coverage invocation mistyped the module separator, collecting no data
  and exiting1 despite43passing tests. This is not reported as coverage success.
- Corrected focused coverage passed:43tests,100% line and branch coverage
  (65statements,12branches); Ruff and strict typing passed. Independent review
  found no actionable production finding; tests additionally compare every
  fact and disposition directly with parsed original rows.
- Cold mutation of the full43-test selection killed33/33 mutants, with zero
  survivors/cache hits and no coverage filtering or pardons, in202.30seconds.
  Report SHA-256: `c3796413c7cb1fffe8d3348df43d071513cb04c1c14b07ecccc1bb9d484b8176`.
- Durable native recovery passed on integrated head49af2b6:2,433tests,
  96.99% overall coverage, eight existing warnings,41schemas/31samples,
  71Conductor tracks,9/9parity, all native mutation and supply-chain gates,
  SBOM111components and558MB/s CAS throughput. RuntimeCPython3.14.6;
  four pytest workers, unchanged gates. Log SHA-256:
  `9a6cfd37b45f4982c4a3d2ca28c0d3ff7d68f86ef91670a0817e1fa8b581cd2d`.
  Exit receipt is0. Exact-head hosted assurance remains pending.
- First native session46275 passed pretest gates and collected2,243tests;
  one failure marker was observed around70% progress. After runtime/context
  interruption its session was unavailable, without final exit or traceback.
  Empty pytest last-failed cache is not treated as success. Only two unrelated
  generated timestamp diffs were present and were restored. One distinct
  recovery attempt on integrated main9c609fe uses durable log/exit receipts;
  no test deadline or threshold is relaxed.

Broader Ministry historical editions, verified base/method metadata, canonical
real/per-capita derivation and publication remain pending; this does not
complete the wider Phase1.2 or Phase5 obligations.
