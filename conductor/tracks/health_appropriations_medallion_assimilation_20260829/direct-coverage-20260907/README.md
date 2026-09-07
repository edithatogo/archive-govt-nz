# Bounded direct-source coverage report

Phase 5.4 reporting component: M-02/M-11/S-04, AC-09/AC-11/AC-16.
Base `917cbd449678f50b2f048f799462ae1ad226ad8b`; isolated branch
`codex/health-direct-coverage-20260907`. Parent owns shared lifecycle,
independent review, integration and full assurance. No source acquisition,
classification/area mapping, CPI/QES work, promotion or publication occurs.

## Input and claim boundary

`direct_coverage.coverage_report` consumes explicitly pinned immutable JSON
bytes: a versioned target register, native health-capture-manifest/v1 receipt,
and an explicit target-ID to extraction-manifest map. It opens no files or
network connections. It verifies metadata bytes, not CAS, WARC, Parquet data,
original source semantics or a whole-programme census. Pins are caller-chosen;
they do not authenticate the producer or prove freshness.

Each input is capped at 4 MiB; total supplied bytes at 16 MiB; target, capture
and extraction counts at 1,000. Strict UTF-8 JSON rejects duplicate members,
nonfinite constants, invalid shapes and redacts contract errors. Exact target
keys, unique target/source IDs, same ISO cutoff, exact source-ID/locator,
source-object digest, object-ID/byte-count consistency, vintage and supported
family/schema joins are checked. Counts must be nonnegative bounded integers,
not booleans; a passed receipt cannot declare rejected rows. This is validation
of consumed receipt fields, not full native manifest or output-table validation.

Targets identify expected source-family/vintage occurrences; unknown vintage is
null, which cannot admit an extraction. URLs are exact strings, not fuzzily
normalized aliases. Multiple target occurrences of one source ID require a
future observation/version contract; this version rejects them as ambiguous.
Vote Health targets can be reported, but no Vote Health extractor schema is
invented. Unselected capture rows receive source-ID uniqueness checks only.

Discovery, capture, extraction and their rights are independent observations.
No capture/extraction receipt gives null and a `*_receipt_not_supplied` gap,
never inferred unavailability. A restriction or withdrawal can coexist with
retained bytes and a previously produced extraction; the report preserves both
without asserting chronology, current usability or rights approval. Missing
rights remain null; supplied rights remain verbatim. No supersession edges,
classification mappings or numeric compatibility are inferred. Counts are
receipt assertions, not independently recounted records.

## Retained pilot

`targets.json` selects eleven direct official expansion entries from the
existing `source-census.json` (SHA-256
`4bea6001b0a1af4a362075508c521befe5bd6e04d20b2dd2f7c23ef8c6256964`).
The explicit vintage labels match the selected retained manifests where
available; no label asserts an independently qualified analytical definition.
This is NOT the entire annual target register: Vote Health's document history,
older Budget/forecast editions and all contextual/mapping work are outside this
pilot. The production report can represent absent supplied capture/extraction
receipts, but the pilot does not invent historic absence evidence.

All eleven target sources have captured receipts. Seven have explicitly supplied
passed extraction manifests. Four have null extraction state: BEFU charts,
BEFU economic forecasts, Budget revenue and HYEFU charts. This means no receipt
was supplied to this report, not proof no derivative exists anywhere. All eleven
capture rights receipts say eligible; all seven extraction receipts independently
say not_evaluated. Neither is converted into a new rights decision.

`replay.py` pins the native capture and seven retained extraction manifests.
It requires the target-register digest separately:

```sh
PYTHONPATH=src python -B conductor/tracks/health_appropriations_medallion_assimilation_20260829/direct-coverage-20260907/replay.py \
  /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations \
  402389ed59038e2e709621a408b05a5a2ec4352c8c380ef9fd36532fc33e49e9
```

Two independent subprocess executions exactly reproduced retained-report.json;
all nine metadata input hashes were identical before/after. The recipe is an
explicit local read-only pilot, not a new operational CLI. No original or
derivative payload was parsed by this coverage replay.

## Concrete repair decision, not approval

`repair-decision.json`, SHA-256
`5dd268440e93fc44d0abe2f99f51031565ad892c8007e63ff14c635fd0c89083`,
contains exactly the 30 existing historical deviations, with exact values,
record IDs, annotated year labels, source coordinates and both observations.
It is a decision exhibit, not a new source dataset or approved repair ledger.
The executable test binds every value to the existing donor-parity receipt's
value hashes and all 30 identities/coordinates/reasons to its deviations.

Decision scope for the accountable user:

1. Restore the 29 annotated Health years 1987–1996 and 2001–2019 in the separate
   source-faithful derivative: Spending!H20:H29 and H34:H52. Donor values are
   absent, not zero; exact values and annotations are in the packet.
2. Retain the literal 1976 Spending!H9 value 605.70000000000005000 million
   instead of representing it only by donor scalar 605.7; exact difference is
   0.00000000000005 million. This is stored-source precision, not an assertion
   of economic significance or an unexplained rounding repair.
3. Preserve the original donor SQLite and prior published products unchanged.
   This decision would not authorize rights changes or publication.

Suggested question: approve both source-faithful changes for this exact packet
(recommended), approve the 29 restorations only, or defer both? Approval is
still `pending_human_decision`; no option has been selected by the agent.

Independent read-only verification during packet preparation checked the
comparison Parquet SHA-256
`a36680aa6225484fd4a44a3d28762ce20abbff621e830db3c758a701fbd2b2f5`,
then read the pinned original workbook
`769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d`.
Direct OOXML workbook relationships selected the Spending sheet; all 30 cell
numeric tokens equalled the packet's Decimal values. The pinned donor SQLite
`a2f9973846e1213823b499e4a019d314485110e80e4ee5a8984ebf3f35c85c8e`
was deserialized into an in-memory query-only connection: all 29 years were
absent and the 1976 donor scalar matched 605.7. No original was rewritten.

## Tests, failures and review

Initial red: missing direct_coverage module, collection exit 2. Initial green:
13 tests; expanded state/null/security cases reached 29 tests, 100% line/branch
coverage and 62 cold mutant kills. Review added aggregate bounds, strict cutoff,
nonfinite JSON rejection and object-without-hash contradiction checks, plus
family, retained evidence and property contracts. An initial pilot register
used shorthand Fiscal-2025; preflight inspection corrected it to the exact
existing Fiscal-Time-Series-1972-2025 label before retaining report evidence.
Initial Ruff/typing failures were fixed, not excluded; only the standalone
recipe has the repository-standard implicit-package exemption.

Final focused selection: 55 dedicated tests, 79 including existing census and
donor-parity tests. Module coverage is 129/129 statements and 30/30 branches.
Cold unfiltered mutation: 69 killed, zero survivors, zero cache hits. Ruff,
formatting and strict basedpyright pass. Mutation's previously-imported-module
coverage warning is retained; the separate measured coverage run passed.

```sh
PYTHONPATH=src python -m pytest tests/domains/health_appropriations/test_direct_coverage.py tests/domains/health_appropriations/test_census.py tests/domains/health_appropriations/test_donor_parity.py --cov=archive_govt_nz.domains.health_appropriations.direct_coverage --cov-branch --cov-report=term-missing -q
PYTHONPATH=src python -m pytest tests/domains/health_appropriations/test_direct_coverage.py --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/direct_coverage.py --gremlin-report=json --gremlin-clear-cache --gremlin-no-coverage-filter --no-cov -q
```

Self-review checked scope, explicit gaps, immutable byte pins, duplicate and
contradictory joins, redacted failures, bounded memory, preserved unknowns and
separate approval states. No shared plan/runlog/metadata/registry changes.
Whole-family/vintage census closure, actual payload verification, semantic
promotion, aggregate Phase 5.4 acceptance, parent full assurance and accountable
repair approval remain separate. No full harness, push or publication ran.
