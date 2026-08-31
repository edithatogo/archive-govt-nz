# Budget source-label classification occurrences

`project_budget_classification` is a pure projection of caller-verified
Budget-expenditure/v1 tables, not a package reader or authoritative crosswalk.
The supported vintages are Budget-2025 and Budget-2026. It reuses the existing
pure Budget reader consistency checks for fact identities, raw labels, named
field lineage and row dispositions; no source or package path is opened.

One `classification_dimension` occurrence and one `field_lineage` record are
emitted per input appropriation fact. Equal labels are not pooled. Identity
binds the rule, caller-supplied manifest pin, source object, vintage, original
fact identity and original coordinate. The exact literal labels are Health,
Core Government Services, No Functional Classification, and Social Security
and Welfare. The latter missing-classification phrase remains a literal label,
not null. Unknown or rewritten labels fail closed.

The scheme is a local source-label scheme, not an official classification
system. Scheme version and normalized identifier remain null; mapping state
is `unmapped`. No valid-time interval is inferred from appropriation years.
Rights remain `not_evaluated`. Every input lineage row is explicitly accounted
as mapped or retained-only; other source fields remain in the unchanged input
package. This is narrow M-05/M-06/M-07 progress, not completion of those phases.

The caller must verify and retain the input package and original bytes before
using this pure function. Its receipt explicitly says fixity is not performed,
authoritative mapping is not performed and publication approval is not granted.
No canonical package is persisted and no existing publication is changed.

## Assurance

The initial absent-module red test failed collection before implementation.
Functional checkpoint `fe618a9` was integrated with main `2061098` before
assurance. Independent read-only review found no actionable correctness issue;
its two optional identity and exact Parquet-round-trip tests were added.

42 focused tests pass with 100% critical line and branch coverage (68 statements,
10 branches). Ruff and basedpyright pass. The cold mutation run killed all
29 generated mutants, with zero survivors, errors, timeouts, pardons or cache
hits, in 25.06 seconds. No coverage filter was requested. Mutation report SHA256:
`304cb972339f4c566d6ce840afca39a67532db641ce4d9f2fc8c1bfe32d08d00`.
Source SHA256: `a48b62b8318cb2e04de924c11436b54d4e2719e54c0fb3838ccd152e331a1f43`.
Test SHA256: `f8f623e3c4481732d28c5e504abbccbc07b46411e54f9540cb02438efa167b99`.
Native repository validation and exact-head hosted delivery remain pending.

## Read-only retained-package reconciliation

Two in-memory builds per retained package were independently compared, including
exact labels/coordinates and complete lineage accounting. All four input package
files remained byte-identical. The audit script SHA256 is
`319daa071bd9921c57d97e56f8dd12a2c524dc76ff90a33c0672b242a65ad726`.

| Vintage | Input manifest SHA256 | Occurrences | Mapped lineage | Retained-only lineage |
| --- | --- | ---: | ---: | ---: |
| Budget-2025 | `1b1e5dfd3fa90d98dcf5200997001db236df7b40f4404b658c36f5cb0264d2fe` | 215 | 215 | 3440 |
| Budget-2026 | `f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738` | 185 | 185 | 2960 |

Together these preserve 400 label occurrences and account for all 6800 original
lineage rows. Byte-identical Parquet serialization was checked in memory only.
The original source objects remain respectively
`d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338` and
`3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0`.
No source download, new rights determination or Hugging Face call occurred.
