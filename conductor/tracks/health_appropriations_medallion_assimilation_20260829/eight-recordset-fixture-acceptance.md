# Eight-recordset fixture acceptance — 2026-09-07

**Historical assessment, superseded:** see
[fixture completion](./eight-recordset-fixture-completion.md). The initial
blocking interpretation below conflated fixture verification with live/source
qualification. Linked fixture and approved adapter assertions now complete the
original fixture task locally; parent retains integrated checkpoint assurance.

Phase 3.1's original broad fixture task remains pending (`[~]`); this is not
a substitute completed task. Requirement mapping: M-05, M-06, M-18; AC-05,
AC-16. Base: `0526365a48f58d241d52a301a901760147cc3eee` (PR407).
Parent issue remains #205. No hosted changes were requested or performed.

The new independently declared synthetic JSON fixture expands common, fact,
recordset and observation fields without deriving expected rows from production
schemas. All eight named recordsets have two observations. Tests use existing
`normalize_json`, `normalize_rows` and `validate_table`; no production code or
dependency changed. Parquet fixtures are generated in memory and replayed,
avoiding environment-dependent committed binary files. Repeated bytes are
compared within the same environment only.

## Full task coverage assessment

| Planned dimension | Executable coverage | Remaining acceptance |
| --- | --- | --- |
| Eight recordsets / JSON Schema / Arrow / Parquet | Exact eight-name census, standalone schema validation, independent typed oracle for every field, metadata equality, repeated Parquet replay | Source-specific canonical projections and package qualification are not established |
| Versioning | Fixed v1 fields and metadata; bad row version and unknown API version rejected for all eight | Future migration policy is outside this fixture task |
| Stable IDs | Supplied IDs survive replay and reversed input order; duplicates rejected across all eight | Arbitrary non-derived IDs still admitted; source-key derivation/collision semantics unverified |
| Fixed precision money | All five fact families preserve Decimal and original lexical value; overflow and excess declared scale rejected | No official source value or unit interpretation is attested |
| Null reasons | All five planned categories across all five fact families; unexplained null and reason on nonnull value rejected | Reason vocabulary is not enforced by the normalizer |
| Units / price / denominator | Monetary NZD-million and index-point contexts preserved; absent unit/base/denominator not manufactured | Ambiguous units and real-without-base remain admitted; no semantic source qualification |
| Vintages | Two explicit vintages and observation IDs retained without sorting or replacement | Vintage validity and source revision identity unverified |
| Bitemporal fields | Explicit financial-year endpoints, UTC microseconds and null unknown dates preserved; reversed interval rejected | Period token/date/status agreement and cross-source temporal alignment unverified |
| Rights | Unevaluated and restricted labels retained; no rights promotion | Arbitrary rights claim admitted; no rights-evidence validation |
| Lineage / classification | Coordinates, raw/normalized values, target and classification slots preserved; null required lineage rejected | Dangling lineage/target/classification and unsupported mapping admitted; no complete field-to-Bronze closure or hash fixity |
| M-18 / AC-16 | Focused schema suite, lint, format, type checks and self-review pass | Parent owns full integrated harness, coverage, mutation, security and supply-chain gates |

Gap characterization tests deliberately assert current admission behavior.
They are not approval tests or expected-failure suppressions. If a later
semantic validator rejects these examples, update the tests and this matrix
together. Synthetic hash strings and example.invalid locators never assert
that Bronze objects exist. The lineage examples illustrate field transport,
not a complete package graph; some cross-observation references intentionally
remain unqualified. Source-family negative fixtures elsewhere do not establish
universal semantics for this additive eight-recordset boundary.

## Validation and review

New test: `tests/schemas/test_health_recordset_fixture_acceptance.py` (142 cases).
Fixture: `tests/fixtures/health-eight-recordsets-v1.json`.
Machine receipt: `eight-recordset-fixture-validation.json`.

Commands run from the isolated worktree, with the existing interpreter used
read-only and `PYTHONPATH=src` selecting this worktree's production code:

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/schemas/test_health_recordset_fixture_acceptance.py -q --maxfail=1
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/schemas/test_health_recordset_fixture_acceptance.py tests/schemas/test_health_recordset_normalization.py tests/schemas/test_health_recordset_json.py tests/schemas/test_health_recordsets.py -q
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff check tests/schemas/test_health_recordset_fixture_acceptance.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff format --check tests/schemas/test_health_recordset_fixture_acceptance.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/basedpyright --pythonpath /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python tests/schemas/test_health_recordset_fixture_acceptance.py
git diff --check
```

Red: missing fixture produced one FileNotFoundError before fixture addition.
This is fixture-contract red, not a production defect; existing normalization
behavior is explicitly characterized. Green: 335 affected tests passed in
2.12 seconds. Ruff found four non-raw regex patterns; corrected and checks
passed. An attempted `ty` command was unavailable; the configured basedpyright
check then passed with zero errors/warnings/notes. No dependency installation.

Self-review: all added fields are independently declared; exact decimals and
UTC dates have independent expected values; corrupted Arrow rows are checked
before and after Parquet for representable corruptions. No production changes,
network, sensitive payloads, global registry edits or original dirty tests.
Applicable general/Python guides: pass after formatting/lint correction.
No selected platform guide applies to this local Python fixture-only change.
No unresolved in-scope implementation defect; broad semantic acceptance remains
open as detailed above. No phase/track completion, full-harness pass, push,
merge or publication claim.
