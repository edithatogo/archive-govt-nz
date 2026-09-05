# Read-only SQLite inventory path and identifier repair

The existing `formats.inventory_sqlite` adapter now opens the resolved path's
encoded file URI with `mode=ro`, and quotes schema-provided table identifiers
by doubling embedded quotes. Its output shape, ordering, source schema text,
integrity result and row-count semantics are unchanged.

Before the fix, a literal `#` in a filename became a URI fragment and could hide
the read-only query option. The regression test observed an unintended alias
database in its temporary directory. Literal `%23` could select another path;
quoted table identifiers could produce SQL parse errors or target the wrong
table expression. No retained source was used or modified during reproduction.

Nine synthetic tests cover literal `#`/`%`/space paths, embedded quotes, SQL-like
and Unicode table names, reserved words, missing-source noncreation, actual
read-only enforcement, byte preservation, deterministic output and connection
closure. The connection spy is scoped to the adapter namespace so coverage and
mutation tooling retain their independent SQLite connections.

This is a structural inventory repair in Phase 3.2, not a new SQLite fact
normalizer, a 312-row parity result, a source-hash verifier or a hostile-database
sandbox. Normal SQLite journal semantics are retained; no `immutable` flag is
used to skip possible journal state. Concurrent replacement and WAL sidecar
policy remain part of a future verified-snapshot adapter contract. PDF-table
extraction and the general multi-format protocol remain pending.

Full combined repository validation stays with the parent. The focused matrix
and mutation outcome are recorded in `normalization-admission-validation.json`;
original main fixture edits, the global registry and other worktrees are outside
this change.
