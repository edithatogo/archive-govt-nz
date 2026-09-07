# Phase 3.2 — donor-SQLite library admission boundary

Isolated branch `codex/health-donor-boundary-20260907`, based exactly on
`b70ddf75594da985f01938cf4724be7e019a416d`. Scope: the existing donor SQLite
normalization library, not eight-recordset reconstruction, new extraction,
CLI CAS verification or source qualification. Shared plan/runlog/metadata and
parent checkout were not edited. This dedicated receipt is the slice's evidence.

## Requirement and pre-implementation audit

Read the complete Health requirements/design and Phase 3 plan. This increment
supports Phase 3.2 safe SQLite interfaces (M-03/M-04/M-05/M-07; AC-02/AC-03/
AC-04/AC-05) and Phase 3.3 determinism/Phase 3.4 local assurance (M-18; AC-16).
It does not complete the broad multi-format task or Phase 3 checkpoint.

`silver.normalize_donor_sqlite` trusted the supplied digest, interpolated the
source path into a URI, checked only table names, fetched all rows without a
bound, and reused output directories/files. `donor.py` handles pinned Git/CAS
preservation and reconstruction, not SQLite normalization; it needs no change.
`tools/build_health_silver.py` already verifies the CAS object before calling
the library; it is unchanged. Direct library callers still need hash-bound
admission at the bytes actually consumed.

The donor parity reader already provided capped, hash-verified memory snapshots,
query-only/trusted-schema controls, integrity checking, row limits and the
integration's `table_xinfo` fix. Importing the oracle from Silver would couple
normalization to comparison/repair models and transitively load Gold plotting.

## Shared design and preserved contracts

Extracted `donor_sqlite.py` as a small layer-independent reader with the existing
fixed table definitions. `donor_parity.read_database` consumes its returned rows
and retains the existing type-tagged digests/repair semantics. Gold re-exports
the same `_TABLE_DEFINITIONS` alias, so existing consumers keep their contract.
No plotting or comparison dependency is imported by Silver through this reader.

The reader opens the literal source path once, reads at most 16 MiB plus one
sentinel byte, verifies SHA-256, and deserializes those exact bytes into a
query-only in-memory connection. SQLite never opens the source pathname as a
URI or consults its journals/sidecars. A changed source after that read does
not change the normalization input; the receipt identifies the verified
snapshot, not future filesystem state. Missing paths are never created.

Admission preserves the approved oracle's exact table-object and column
signature: all five table names and no views/indexes/triggers, with ordered
column names, declared types, null/default/primary-key and hidden/generated
markers from `table_xinfo`. Virtual and stored generated columns are rejected.
This is schema-signature verification, not lexical CREATE TABLE equivalence or
a new general SQL schema parser. The integrity check, SQLite value-length cap
and VM-work bound are retained. Row queries have explicit rowid order and fetch
only the remaining aggregate 10,000-row budget plus one sentinel; they cannot
silently truncate or discard duplicate occurrences.

Silver retains its existing v1 fields, IDs, decimal/date mapping, raw JSON,
lineage and rights defaults. No new semantic/source promotion is asserted.
It builds typed Arrow tables before reserving a new output directory, then
opens each fixed output filename exclusively. Existing empty, complete or
partial output directories fail closed. Interrupted output is retained and a
retry must use a new destination. A racing file within a newly reserved
directory is not overwritten. No automatic cleanup or replacement is added.
These are trusted-local-path controls, not a hostile-filesystem/process sandbox
or a power-loss durability claim.

Compatibility changes are intentional: direct callers must supply the real
digest and a new output directory. Schema errors now use shared reader classes
such as `database_table_drift` instead of Silver's former table-only class.
The old test fixture's placeholder hash was replaced by its actual synthetic
database digest. The oracle integrity-injection test now patches the shared
reader binding; its verification assertion remains unchanged.

## TDD, focused validation and review

Eight initial tests failed on wrong-hash acceptance, extra/generated columns,
views/indexes, URI-sensitive filenames and output reuse. After implementation,
the new file has 23 cases, including byte/aggregate-row boundaries, invalid
bounds, corruption/missing files, snapshot stability, bounded read arguments,
partial-output preservation, racing-file exclusion and a 13-example duplicate
row-budget property. Existing deterministic Parquet, donor parity and Gold/plot
consumer tests were rerun, not replaced.

Final: **105 affected tests passed**, with **100% line/branch coverage** of both
`donor_sqlite.py` (50 lines/16 branches) and `silver.py` (61 lines/14 branches).
Eight independent in-memory mutants are caught: disabled fixity (2 failures),
unbounded read (1), byte-boundary shift (2), row truncation (3), disabled column
signature (10), disabled object signature (4), directory reuse (1), output
overwrite (1). No mutation edits touched on-disk production code.

Ruff check/format and basedpyright pass. The new worktree has no virtualenv;
type checking required `--pythonpath` pointing to the existing pinned runtime.
Development corrections included test-wrapper typing/style, one displaced test
assertion, and restoring nested-loop indentation during the mechanical
extraction. No weak assertion, exclusion or threshold change was introduced.
Existing unclosed-SQLite ResourceWarnings from adjacent fixture/Gold paths
remain visible; the shared reader closes its memory connection in `finally`.

```sh
PYTHONPATH=src COVERAGE_FILE=build/silver-boundary.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_silver_boundary.py tests/domains/health_appropriations/test_silver.py tests/domains/health_appropriations/test_donor_parity.py tests/domains/health_appropriations/test_donor.py tests/domains/health_appropriations/test_gold_reader.py tests/domains/health_appropriations/test_plot_export.py --cov=archive_govt_nz.domains.health_appropriations.donor_sqlite --cov=archive_govt_nz.domains.health_appropriations.silver --cov-branch --cov-report=term-missing --cov-report=json:build/silver-boundary-coverage.json -q
```

Conductor self-review found no remaining actionable issue within this requested
boundary. Full integrated assurance and independent review belong to the parent.
The broader adapters, dimensions, source semantics and Phase 3 checkpoint are
not completed by this slice. No full harness, live acquisition, publication,
shared registry/plan/runlog/metadata or original-checkout changes occurred.
