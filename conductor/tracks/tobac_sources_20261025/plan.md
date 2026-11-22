# Plan

- [x] Inspect archive contracts, consumer provenance and estate inventory.
- [x] Register 43 references and 18 consumer CSVs without changing source meaning.
- [x] Execute bounded native captures and explicit challenge/identity postflight.
- [ ] Complete blocked source retrieval and full-text/attachment qualification.
- [ ] Qualify remote raw-object recovery and source-specific redistribution.

## 22 November 2026 — registry identity and source-set reconciliation

The exact pre-reconciliation register observed at repository revision
`e987d4121473d5d07b65f7a6f29753f361a36041` is retained byte-for-byte at
`registry/tobac/snapshots/sources-aa61424788e60053683a6b78fdce0d1cd29ed174f9520c8ef5f54abdbca72114.json`.
Its SHA-256 matches the hash recorded in the unchanged dated
`evidence/tobac/capture-bindings-20261025.json`. This does not establish that the
58-row snapshot was the original 25 October capture register. The dated binding
has 50 rows and is not full acceptance or coverage of the current registry.

The live registry consolidates the byte-equivalent Customs OIA 25-083 duplicate:
`tobac-b1fa936032744c5cae` maps to retained ID `tobac-10cecc3dcc6a40649b`.
The retained ID was introduced in [6e5b6a14](https://github.com/edithatogo/archive-govt-nz/commit/6e5b6a145497cf436ec6f85da46b3bc73b1b2ced);
the duplicate was introduced as a re-entry in [64017930](https://github.com/edithatogo/archive-govt-nz/commit/640179302461a75c7933bb16c15d0df3fa255c60).
Both IDs' pre-reconciliation content remains in the immutable snapshot. The
current registry has 57 unique records and the same 61 distinct source URLs.

The existing source-set target list is reconciled directly from the canonical
registry using installed JSON/YAML tooling, preserving its original target order
and all non-target metadata. Scheduling remains manual; Hugging Face and Zenodo
publication remain disabled. Existing assertions retain exact current URLs,
unique current aliases and the same dated binding hash equality, now checked
against its retained registry version. No capture, source qualification,
publication, historical binding change or capture re-verification occurred.
