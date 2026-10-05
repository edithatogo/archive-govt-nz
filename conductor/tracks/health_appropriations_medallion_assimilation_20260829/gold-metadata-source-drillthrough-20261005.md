# Gold manifest source drill-through

Metadata schema v3 adds a separate `source_drillthrough.json` projection for
references that the verified Gold package manifest explicitly records. It
copies only the `source_manifest_sha256`, `source_object_sha256`,
`raw_manifest_sha256`, and `*_source_url` / `*_definition_url` fields. Each
record names the exact JSON field path and binds to the enclosing Gold manifest
SHA256. No references are inferred from neighboring labels or table contents.

The projection labels URL values as recorded locators only. It does not claim
that they are current, accessible, licensed, or redistributable. Rights remain
`not_evaluated`; publication remains `not_performed`. The Fiscal analytical
manifest supplied 18 recorded references. The Budget comparison manifest had
none, so its record carries
`source_reference_fields_absent_from_package_manifest` rather than a fabricated
link. Approved partner federation links remain absent.

## Actual-package evidence

Two independent CLI builds used Fiscal analytical manifest
`1b79d6f582dc8e9935e16bce2d3fe78b78d77e2a68aacf201ac9118b28462fa2` and Budget
comparison manifest
`e8c7efda7773368bcee1b7f596f373c0aa6ec3f4453485b9b6fb9cc447ebd5fc`. Both
produced metadata receipt SHA256
`8a29a0acbec71e3a50a6c5c2b121d72711a25405d7e02fe1895a80902cbc68c1`, and all
nine output files were byte-identical. The retained output is
`assurance/gold-metadata-20261005-v2/first` under the external Health
Appropriations evidence root. The source-drillthrough payload SHA256 is
`d70594f2eda9eba4ef666fd1e4ff5c6a332fe6ad1c61ddcbba0c2a2c36ce7fc7`.

The payload validates against its closed JSON Schema, and an independent
readback resolved all 18 Fiscal reference paths against the exact pinned source
manifest bytes. The Budget manifest pin was reverified and contains no matching
source-reference fields. Focused metadata tests passed (3 tests); the repository
schema validator passed (56 schemas, 46 representative documents). The full
`./scripts/validate.sh` passed: 7,489 tests passed, 10 skipped; typing, schema,
parity, mutation, hygiene, benchmark, dependency, licence, secrets and SBOM
gates passed. Coverage was 97.75%, above the configured 80% floor.
