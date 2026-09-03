# Persisted Budget provenance verifier

This bounded extension admits the local-only Budget appropriation package to the
existing read-only provenance verifier. It requires the exact six-file closure:
the appropriation fact, classification dimension, field lineage, full projection
receipt, line-delimited original-lineage accounting, and `LOCAL_BUDGET.json`.

The verifier independently pins the marker, raw manifest and original workbook;
uses the public bounded Budget reader; recomputes the public canonical projection
under a fresh decimal context; and requires exact Arrow values, schema metadata,
receipt, accounting, file hashes and marker claims. Repinning changed output
cannot make it a valid projection.

The pure inventory admits only Budget-2025/2026 for this profile. It records the
appropriation fact as dependent on its same-package classification dimension and
field lineage as dependent on both canonical data tables. The dimension has no
canonical product dependency. The package cap expands from four to six only to
permit two vintages of each delivered historical, classification and Budget
profile; roots and `(kind, vintage)` pairs remain unique.

This is Silver snapshot verification, not later disk-state monitoring, hostile
filesystem transactionality, rights review, standards conformance, authoritative
classification, publication approval, Hugging Face publication, or complete
Bronze-to-Platinum acceptance. It returns metadata rather than a public row
snapshot, so the persisted canonical consumer API remains future work.

Focused assurance passes 135 composed inventory/reader tests with 100% coverage
of 268 statements and 44 branches. Ruff and basedpyright pass. Cold mutation,
retained-package verification, final predecessor integration, native assurance
and hosted delivery remain separate gates at this checkpoint.
