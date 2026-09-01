# Legislation source-set contract

`config/source-sets/legislation.yml` is the versioned execution contract for
legislation acquisition. Version 2 is validated against
`schemas/source-set-v2.schema.json` and represented by immutable typed models in
`archive_govt_nz.source_sets`. YAML is parsed with a safe duplicate-key rejecting
loader; unknown fields, unsupported versions, ambiguous names, invalid types and
cross-field contradictions fail before an acquisition client is created.

The contract separates capability from activation. An adapter, preservation
format or publication destination may be declared without being active. Active
features must be supported. Publication additionally requires approved rights,
an attributable decision, enabled external actions and both publication gates.
The checked-in configuration keeps Hugging Face and Zenodo inactive and performs
no publication or metadata migration.

The `scope.type` value is authoritative. `discovery` accepts bounded search
terms. `exact_inventory` accepts only the canonical newline-delimited inventory
whose count and SHA-256 match the configured seed scope. These modes cannot be
silently interchanged. Neither is a full legislative coverage claim.

The scheduled harvest runner and the direct `legislation discover/sync` CLI both
load the shared contract before acquisition. They enforce the configured lane,
work bound, acquisition gate, active adapter, checkpoint authority and, for an
exact inventory, its count and hash. The runner also requires active CAS and
manifest preservation, uncompressed canonical state and SHA-256 fixity. Generic
source-set capture reads typed active adapters without treating inactive or
merely declared entries as executable.

Known unversioned legislation v1 documents can be migrated in memory when their
top-level and nested shapes match exactly. Migration preserves disabled state and
never activates publication. Other shapes and future versions fail with a field
path and rule name while omitting controlled values. Operators should migrate by
copying the v2 sample matching the intended lane and then validate it:

```console
uv run --locked python tools/validate_schemas.py
uv run --locked pytest tests/test_source_set_contract.py
```

Samples are available at `tests/fixtures/source-set-discovery-v2.json` and
`tests/fixtures/source-set-exact-inventory-v2.json`. The exact-inventory sample
shows the stable reviewed seed identity and hash contract; it does not execute a
schedule or authorize acquisition.
