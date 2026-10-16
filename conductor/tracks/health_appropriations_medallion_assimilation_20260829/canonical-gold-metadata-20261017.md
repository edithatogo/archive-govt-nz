# Canonical Gold metadata profile

M-14, M-15, M-18; AC-13, AC-14, AC-16. Related issues: #205, #213, #214.

The existing local metadata projector now accepts the explicit
`canonical_source_separated` GoldInput profile. It verifies the pinned canonical
package and every selected fact table through the shared bounded typed reader.
The eight supported products retain their full Arrow schema and literal observed
period tokens; metadata is not built from the query API's capped row sample.
Token values are not converted into dates, chronological bounds or continuous
coverage. Descriptors are collected one decoded table at a time.

The existing catalogue, schema descriptors, DCAT/PROV graphs, local citations,
snapshot changelog, source-reference projection and composite dataset card are
reused. The canonical producer's card and RO-Crate remain input inventory
members when present; they are not replaced. Only explicit manifest source
reference fields are copied, with absence recorded. Rights remain unassessed,
publication unperformed and approved federation links absent. This does not
qualify full standards conformance, resource redistribution or source accuracy.

## Schema and invocation compatibility

Canonical-containing metadata uses `archive-govt-nz.health-gold-metadata/v4`
and source references use `archive-govt-nz.health-gold-source-drillthrough/v2`.
Separate citation/changelog/source-reference schemas and representative fixtures
cover those versions. Existing v3/v1 schemas and Fiscal/Budget projection bytes
are preserved unchanged; they are not widened under their existing identifiers.

The existing `health-appropriations-build-gold-metadata` and
`health-appropriations-verify-gold-metadata` CLI commands accept optional
`--canonical-package` / `--canonical-manifest-sha256` alongside their established
Fiscal/Budget arguments. The read-only
`health_appropriations_verify_gold_metadata` MCP tool accepts the same optional
pair. Both fields or neither are required; partial pairs fail before package
processing. Existing two-package invocations retain metadata v3, while a
three-package composite uses v4. Canonical-only projection is supported by the
GoldInput API; the composite CLI retains its established required inputs.

## Verification

- 92 focused metadata/query/CLI/MCP integration checks pass (48.24s).
- The full-table fixture contains 300 historical rows, exceeding the query cap;
  every literal token and exact Arrow schema is retained. Wrong pins, schema
  drift and unsupported rights states fail closed.
- Installed native CLI dry-run, exclusive write and verify match the initialized
  read-only MCP receipt. Both half-pair forms are rejected. Inputs are unchanged.
- Relevant Ruff/format and focused typing pass. Schema validation passes for
  59 schemas / 49 representative documents; Conductor reports 93 tracks and
  no errors.
- Native projection covers 13 recordsets / 1,184 rows across three Gold packages;
  eight canonical fact products contribute 800 rows. Every schema and canonical
  token set matches independent Arrow readback. Offline graph interpretation
  finds 13 DCAT datasets and three PROV collections, with external resource
  access denied.
- Two native metadata builds and installed CLI output are byte-identical.
  The pre-change projector loaded from parent `2bfe3614` generates exactly the
  same eight Fiscal/Budget metadata payloads as the current implementation.

Final native metadata manifest:
`4e0de18af3ae6800f9c9ea9596b6e35e906f9f8c71a1544d6bdfc71b999eee9f`.
Native assurance receipt SHA-256:
`17a15f48b943d3c99f766c8819689856fbfe975341bdd32bcfb0b2e716afc76f`.
Native source Gold pins:

- `budget_comparison`: `123fd90613ebb844d41572e3b4d466ebc3d52dbe594a652e96c324dd21755552`.
- `canonical_source_separated`: `2f14fa0930df65f10a835ffa261c920b7331d25c7e8fa72017243239e12084f8`.
- `fiscal_analytical`: `1b79d6f582dc8e9935e16bce2d3fe78b78d77e2a68aacf201ac9118b28462fa2`.

Retained native packages/receipts are under
`/Volumes/PortableSSD/tmp/canonical-gold-metadata-20261017/native-v4/`.
Reproduction scripts/logs are `native_v4.py`, `native_surface_v4.py`,
`native-v4.log` and `native-surface-v4.log` in the parent directory. Earlier
`native/` receipts precede the schema-version correction and remain historical
failure/review evidence, not final receipts. Metadata verification rechecks
Gold, not Bronze or original-source meaning; this is not full track recovery.

Required `./scripts/validate.sh` passed on implementation
`b2fde77e67555913f5a32369f9253ed1260c210e`: 7,698 tests passed, 10 skipped;
97.43% coverage against the 80% floor; 59 schemas/49 representative documents;
parity 9/9; all mutation, hygiene, security and supply-chain gates passed,
including the 113-component SBOM. Conductor reports 93 tracks and no errors.
Session 9819 and the durable `validation.exit` record exit 0. The subsequent
commit records evidence/task status only; hosted checks must qualify the final
PR head before protected merge. The broader Platinum, operations, source/rights and final track gates
remain open.

## Protected delivery

PR #690 final head `fe688927fe7dec9b0d3af6c501059159c0990c9a` passed all required
platform/security/lint and patch coverage checks. It merged normally as
`3f6f6f012a9a4bc2eb6270ec9b0f012d35ec06cd`, was verified on `origin/main`, and
its clean local/remote topic branches were pruned before the recovery slice.
