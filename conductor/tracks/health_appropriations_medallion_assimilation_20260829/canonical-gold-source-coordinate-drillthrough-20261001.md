# Canonical Gold source-coordinate drill-through

The canonical Gold manifest now links each admitted input record to both its
deterministic Gold row locations and the exact source-field coordinates carried
by that record's verified canonical `field_lineage` table. Each source-coordinate
entry retains the field, coordinate, source-object SHA-256, source vintage and
recorded rights state. It carries a SHA-256 digest of the source locator rather
than copying locator text into the Gold report.

The exporter re-reads lineage through `read_verified_canonical_tables`, which
checks the retained canonical package against its original and raw source
package before emitting the coordinates. Coordinate entries are sorted by
vintage, source-object digest, coordinate and field for deterministic output.
The drill-through contract is versioned as
`archive-govt-nz.health-source-drillthrough/v2`.

The focused canonical Gold contract suite passed 16 tests, including checks that
every exported input record has source-coordinate evidence and every Gold row
link resolves to the pinned Parquet bytes and row identity. Repository coverage
remains governed by the existing 80% floor; these checks protect the new
lineage contract rather than raise a coverage target.

This adds source-coordinate lookup evidence. It does not re-open source bytes at
each coordinate, establish legal rights, publish locator text, approve
cross-source mapping or close the broader Gold source-health and reconciliation
gates.
