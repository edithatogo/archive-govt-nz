# BEFU 2026 and HYEFU 2025: bounded source-profile pilots

## Reviewed source contracts

The retained originals were read from hash-verified Bronze snapshots without
network access, source modification or formula evaluation. HYEFU 2025 changes
the sheet name from the legacy HYEFU `Expense Tables` to
`Core Crown Expense Tables`; it is not silently routed through the old profile.
BEFU 2026 retains the latter sheet name but receives its own explicit profile.

| Contract | BEFU 2026 | HYEFU 2025 |
| --- | --- | --- |
| Profile argument | `befu-2026/v1` | `hyefu-2025/v1` |
| Required source vintage | `BEFU-2026` | `HYEFU-2025` |
| Sheet | Core Crown Expense Tables | Core Crown Expense Tables |
| Health label / literal values | D9 / F9:O9 | D8 / F8:O8 |
| Year string cells | F5:O5 | F4:O4 |
| Amount-type cells | F6:O6 | F5:O5 |
| Unit label | D6 `($millions)` | D5 `($millions)` |
| Selected years | 2021–2030 | 2021–2030 |
| Supplied types | 2021–2025 Actual; 2026–2030 Forecast | 2021–2025 Actual; 2026–2030 Forecast |
| Worksheet extent | 388 rows × 16 columns | 383 rows × 22 columns |

The versioned guard binds the source-vintage label, Health/unit coordinates,
F:O columns, exact year strings and amount-type sequence. Existing generic
`befu` and `hyefu` behavior and outputs are unchanged. The shared extractor
retains its exact Decimal, partial/rejected input and exclusive-directory
contracts; the new profiles do not introduce formula evaluation or cached-total
selection. `tools/build_health_forecast.py --profile` exposes the two explicit
new choices. No profile is inferred from the filename or supplied vintage.

All twenty selected amounts are literal numeric cells in the originals.
Financial-year start/end and institutional comparability are not inferred;
`financial_year_basis_unverified`, null valid-time start and source vintage
remain on each fact. No vintage-splicing, revision analysis, Gold replacement,
rights approval or Hugging Face publication is performed.

## Original and derivative fixity

- BEFU 2026 original: 193,830 bytes,
  `313ee040abd9a332cc36245da5a0c2cb0d38fe2cedc013d731c1f12db463b0d1`.
- HYEFU 2025 original: 191,581 bytes,
  `f9f9190a69ce0a7c53b89d690d50170e2a6a457e6821afeb93edc08cef4b9c7d`.

Exact source URLs and capture timestamps come from the existing source census.
Each profile was built twice into exclusively new local directories. All four
files agreed byte-for-byte for each profile. Retained archive directories are
`silver/raw-befu-2026-20260831-v1` and `silver/raw-hyefu-2025-20260831-v1`.
No earlier dataset, profile output or original was overwritten.

| Product | BEFU 2026 SHA-256 | HYEFU 2025 SHA-256 |
| --- | --- | --- |
| Manifest | `83bd8c0d661383712ade0e7ec1c14bb7cbdba9c93a83df74abbfc64a4586afea` | `5ef89741ad695efd078ba7b7dca2a059948c5bc12069fb434c695ad9293083b5` |
| Facts | `d48f94bbd67cd8fd3418fbab9c5ea815c145a228c6e1e35124dba6449c2b8b17` | `747332611ebe24fb8fe11d25602a309d91b7cb886f9c01933744608676d22e1e` |
| Lineage | `c82edf32e930fc991dfce9cefb7dbfdae484ace3be5956ed1800fe3a1e690671` | `13537eb7ae1d046677737803cd5541d271567828374d25e565fccc8e0ab18751` |
| Cell dispositions | `947366215373c1a42c3073ebc059a62f758c8a5d95537cbafc756a7bb963484c` | `d8f10aa5c2a522603918cfe3270ec2965afd9ae54afa1a4bb06b9fcd7ddd01b1` |

BEFU: 10 facts, 60 lineage entries, 2,375 cell dispositions (22 context,
10 normalized, 2,343 preserved only, zero rejected). HYEFU: 10 facts,
60 lineage entries, 2,346 dispositions (22 context, 10 normalized,
2,314 preserved only, zero rejected).

Independent ZIP/OOXML parsing resolved workbook relationships and shared
strings without the extractor/openpyxl. It matched all selected literal
amounts, year/type fields, all 120 raw/normalized lineage entries, and every
one of the 4,721 nonempty/selected worksheet disposition coordinates. Each
worksheet has 400 formula cells, all preserved only; no selected input is a
formula. Original hashes matched before and after the pilots.

The separate Index sheets remain explicitly excluded from normalization but
inventoried and retained in Bronze. Other expense lines, classifications,
formula-based tables and detailed totals remain preserved only, not normalized.
This is not full workbook-area or longitudinal-edition coverage.

## Validation and delivery state

- Twelve red successor tests initially failed with
  `unsupported_forecast_profile`; only then were the versioned guards added.
- Synthetic tests cover both exact profiles, wrong vintage, shifted rows,
  shifted columns/unit, year-value/type drift, Actual/Forecast split changes,
  and selected formula rejection without evaluation.
- Eighteen successor tests pass; the combined legacy/successor suite passes
  all 50 tests with 100% critical coverage (126 statements, 48 branches).
  Ruff and basedpyright pass. Functional checkpoint: `ce509d4`.
- Existing property tests continue exercising exact numeric preservation.
- Cold mutation ran the full 50-test selection: 64/64 mutants killed, zero
  survivors, timeouts, errors, pardons or cache hits. Report SHA-256
  `e7355e561b0f6f98ea8861289a8f00c8bfab2f413bd43246dcd5878f54d2a7b3`;
  production source SHA-256
  `092e7a5052c7df7b2087f50978a7cc061246914f8f34084f7b5a9fc18a612746`.
- Full native `./scripts/validate.sh` exited zero on CPython 3.14.6 with
  `COVERAGE_CORE=ctrace`, `PYTHON_JIT=0`, four pytest workers and unchanged gates.
  1,974 tests passed with eight existing SQLite ResourceWarnings, 96.77%
  overall coverage, 40 schemas/30 documents, 70 Conductor tracks and 9/9 parity.
  All native mutation, hygiene and supply-chain gates passed; CAS throughput
  was 635.44 MB/s against the 25 MB/s gate and the SBOM had 111 components.
  Timestamp-only unrelated generated evidence was restored.
- The full native result predates integration of main `1b2d7c0`. Integration
  preserved both branches' evidence and all incoming ledger lines as a prefix;
  the unchanged forecast source passed all 50 focused tests again (9.46 s),
  and Conductor validation passed all 70 tracks. The full suite was not rerun
  after that integration. Main then advanced to `113bac5` (PR #280); a second
  integration retained its completed Budget tasks and the single identical CPI
  receipt already delivered there, with both forecast receipts appended.
  Exact-head hosted assurance remains pending.
- PR #283 was observed merged at `2026-08-31T12:00:04Z`, merge
  `565dd8845d151dcd31e5b6448e719f05fa12011d`, after all seven checks passed on
  exact head `ececf5ae147eccd8076f18c3727c599e5019eb46` (CLEAN before merge).
  Assurance run `33388902524` passed on Ubuntu, macOS and Windows. This hosted
  result is separate from the pre-integration local full pass above and does
  not imply rights qualification or publication. Broader Phase 1.2/5 coverage
  remains pending.

Work was moved non-destructively to a standalone `--no-hardlinks` clone after
other registered worktrees disappeared externally. The original forecast
worktree and all raw data were left untouched. This is a resilience measure,
not evidence identifying the cleanup actor.
