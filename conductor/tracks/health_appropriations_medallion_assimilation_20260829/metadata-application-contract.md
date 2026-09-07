# Strict local metadata application subset — 2026-09-07

Additive slice from `af5a62a60996fd722641f12a49b87c1a3c1c2ef6`, covering a
bounded part of Phase 7.1 / M-04, M-14, M-18 / AC-04, AC-14, AC-16. No shared
lifecycle files or existing generators were changed. This is not Phase 7 completion.

## Inspection and reuse decision

- `tools/build_health_candidate.py` emits health candidate/v1 manifests,
  calls the domain Croissant generator with a fixed publication date and single
  donor Parquet reference, and emits a minimal RO-Crate graph of File identities.
  It does not supply per-file RO-Crate fixity/version or comprehensive Croissant
  payload binding. Existing historical outputs were not rewritten.
- `candidate_readiness.py` verifies candidate bytes and required metadata presence,
  plus original-resource rights coverage, but does not validate these descriptor
  contents against a strict application profile. Its existing behaviour remains
  unchanged; this new validator is **not wired into release readiness**.
- `schemas/medallion.py`, `distribution/metadata.py` and `dist/packaging.py`
  already generate descriptors. Their date/licence defaults and differing shapes
  must not become evidence of publication, rights or full standards conformance.
  The health domain's current default licence is UND, not blanket CC BY.
- `preservation.validate_ro_crate` is explicitly a minimal structural fixture
  check, not an application validator. Existing local DCAT/PROV verifiers remain
  separate completed capabilities and were not duplicated.

The new module reuses `PublicationItem`, `SCHEMA_VERSION`,
`compute_bundle_root_digest` and the pure `generate_croissant_metadata` helper
from `dist.packaging`. Existing generic code is unchanged. The helper's
`sc:Dataset` lacks an `sc` binding in that descriptor's context; the accepted
local subset uses `Dataset` under the existing schema.org `@vocab`. This is an
explicit application restriction, not an upstream standards-conformance claim.

## Accepted contract

`validate_metadata_application` takes exact in-memory publication-manifest/v2
bytes, its expected SHA-256, an explicit payload dictionary, and separately
pinned rights-assertion JSON bytes. It performs no filesystem/network operation.
It supports only `nz-health-appropriations` with item domain
`health_appropriations`, explicit nonblank manifest identity/version, a recorded
timezone-aware creation timestamp and no configured remote platforms. The supplied
creation timestamp is checked, not generated or treated as a publication date.

Both JSON documents reject duplicate members, malformed UTF-8, BOMs, nonfinite
JSON constants and oversized input. Unknown schema/envelope/item/rights fields
are rejected. Resource identities are bounded portable relative paths; duplicate,
case-colliding and ancestor/descendant paths are rejected. Each exact payload must
match its integer byte count, SHA-256 and BLAKE3; the existing aggregate bundle
digest must match too. Media types remain caller assertions, not magic-byte checks.

Croissant distributions and the RO-Crate File graph must exactly match the
manifest inventory, name and version, including literal local member references,
hashes and RO-Crate sizes. Extra, missing or duplicate nodes, altered contexts,
changed targets and blanket licence/actor/date/access-URL claims are rejected.
JSON number types are distinguished: floating `14.0` is not exact integer `14`.
Arrays follow the manifest inventory order. Relative `contentUrl` values are
existing supplied member identities, not inferred remote access URLs. Contexts
are compared literally and never retrieved or RDF-expanded.

The rights sidecar has schema
`archive-govt-nz.health-metadata-rights-assertions/v1` and exactly one resource
assertion per payload, including derivatives. Each row has `path`,
`payload_sha256`, `state`, `license`, `evidence_sha256`. `unresolved` and
`restricted` have null licence/evidence in this narrow profile; richer negative
rights-evidence models are unsupported. `eligible_asserted` requires a nonblank
licence assertion and SHA-256 evidence reference. Missing, conflicting, extra or
misbound records fail. Mixed states remain per-resource, never blanket licensing.

The receipt pins both input documents and distinguishes verified supplied payload
bytes from **rights assertion consistency only**. Rights evidence bytes and
authority are not checked; even all-eligible assertions cannot grant approval.
Unresolved/restricted inputs can pass *local metadata validation*, never publication
eligibility. No publication candidate, actor, date, licence or mapping is generated.

Limits: 2 MiB per JSON document, 128 items, 16 MiB per payload, 64 MiB aggregate
payloads, 4,096-character text fields and 240-character paths with 80-character
components. These are explicit application bounds, not general standard limits.

## Verification and review

Synthetic TDD: initial six cases failed with `ModuleNotFoundError` before module
creation, then passed. Final **94 new tests / 142 affected tests passed**.
New-module coverage: **138 statements, 14 branches, 100% line/branch**. Fixtures
cover exact pin/identity/version/fixity binding, missing/conflicting rights, mixed
states, typed byte counts, dangerous paths, duplicate JSON, metadata overclaims,
closure, exact bounds, immutable inputs and a no-I/O guard. Property tests exercise
canonical object-key ordering. Fixtures are synthetic; no original or live payload
read occurred and no actual rights decision was made.

Dedicated cold mutation runner: baseline exit 0; **25/25 mutants killed with
pytest exit 1**, not collection errors. Initial four survivors were masked guards:
dataset identity, duplicate JSON, reserved path, SHA-256. Added otherwise-consistent
fixtures to isolate those conditions. Two further mutants bypass each descriptor
comparison. Final rerun killed every mutant. The runner uses temporary source
copies, bounded subprocess timeouts and no repository-source writes.

Ruff check/format and focused basedpyright using the existing sibling environment
pass. A first typing run required explicit casts after runtime JSON shape checks;
tests cast only intentionally invalid runtime values. Self-review tightened exact
descriptor comparison against Python numeric equality (`14.0 == 14`) and rejects
unknown timezone offset `-00:00`. No remaining in-scope blocking finding identified.

No dependency changes, shared plan/runlog/metadata edits, source adapters, federation
mapping changes, full harness, hosted writes, new source capture or publication.
Parent owns integration/full-gate/lifecycle reconciliation.

## Reproduction

Use the existing environment (review runtime Python 3.14.6 at
`/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python`). From the isolated
worktree set `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, and place coverage and
Hypothesis storage in a fresh temporary directory.

```sh
python -B -m pytest -q -p no:cacheprovider \
  --cov=archive_govt_nz.domains.health_appropriations.metadata_application \
  --cov-branch --cov-report=term-missing \
  tests/domains/health_appropriations/test_metadata_application.py \
  tests/domains/health_appropriations/test_candidate_readiness.py \
  tests/schemas/test_medallion_croissant.py \
  tests/distribution/test_distribution_metadata.py \
  tests/dist/test_packaging.py
python -B tests/domains/health_appropriations/metadata_application_mutations.py
```

Run `ruff format --check`, `ruff check`, and
`basedpyright --pythonpath <existing-environment-python>` on the three Python
files pinned in the paired evidence JSON. No new environment is required.

## Exact remaining clauses

- Actual health-candidate/v1 generator/profile migration and release-validator
  integration; this application subset accepts generic versioned manifest/v2 only.
- Source-backed rights evidence/authority verification, redistribution eligibility,
  restricted metadata-only/tombstone policy and accountable release approval.
- Croissant field/recordset source bindings, complete RO-Crate application profile
  and independent standards validation. No full conformance is established here.
- Broader schema-as-code, DCAT/PROV application profiles, cards/citations/changelogs,
  source drill-through and end-to-end actual-layer metadata generation.
- Federation remains outside this slice; Phase 7 review/full gates remain pending.
