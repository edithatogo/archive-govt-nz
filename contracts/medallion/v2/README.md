# Medallion field-lineage vocabulary v2

Version 2 adds checksum-bound field-level lineage without changing immutable v1.
Every record identifies the source dataset and field, transformation, output
dataset and field, content-addressed code version, input/output SHA-256 digests,
and the governing rights decision. Repositories may project conforming records
to PROV-O, RO-Crate, or OpenLineage without importing a shared runtime package.
