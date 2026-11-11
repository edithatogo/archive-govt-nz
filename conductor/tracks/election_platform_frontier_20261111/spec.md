# Architecture and contract specification

## Vertical pipeline
Publisher sources -> immutable Bronze captures (checksums/licence/source vintage) -> validated Silver rows (Pydantic/Arrow/Polars) -> Gold election/margins/projections with input hashes -> deterministic static release manifest -> HF Space. Historical source data remains immutable. Tooling is abstracted for reuse with archive-govt-nz domains.

## Contract: ElectionSourceSnapshot (versioned)
`{source_id, publisher, source_uri, election_year, vintage, captured_at_utc, published_at, sha256, content_type, licence, schema_id, validation_status}`.
Refuse mismatched year/vintage, missing rights or checksum, duplicate identities or partially captured mandatory source objects.

## Contract: ElectionScenario
`{id, baseline_release_id, electoral_rules:{threshold_pct,electorate_qualification,overhang_policy,nominal_house}, party_vote_adjustments, electorate_winners, special_vote_distribution_parameters, random_seed, assumptions, provenance}`.
Validate vote conservation or explicitly label an exogenous electorate-level turnout change. Do not combine inconsistent totals. Do not allow negative party votes or electorate counts.

## Contract: ElectionAnalyticalResult
`{scenario_hash, baseline_source_hash, engine_version, timestamp_utc, outputs, source_status, result_kind, model_validation, diagnostic_summary, uncertainty, warnings}`.
`result_kind` one of observed|derived|estimated|counterfactual|experimental. HTML labels are generated from this contract.

## Contract: Geography
`{electorate_id, boundary_vintage, geometry_hash, coordinate_reference_system, valid_from, valid_to, concordance_version, uncertainty, source_id}`.
Do not compare boundary-vintage counts without reconciliation.

## Contract: ResearchPublication
`{source_snapshot_ids, dataset_hashes, transform_hash, code_revision, py_lock_sha256, model_card_id, figure_manifest, CSL_JSON_references, methods, assumptions, limitations, evidence_checks, release_digest}`.
Use native GitHub artifact attestations/SBOM, reuse archive evidence ledger; do not implement new cryptography when standard evidence suffices.

## Interaction architecture
Static results first; separate browser pages/modules for MMP lab, geography, longitudinal and research. Experimental area visually and semantically isolated. Progressive disclosure, keyboard/screen-reader accessible charts, mobile responsive; no server-side simulation in a static Space without explicit execution gateway.

## Research identification gates
RDD: pre-specified running variable, treatment, bandwidth, density/manipulation and placebo tests; IV: relevance/exclusion/sensitivity; SHAP: predictive attribution not causal; special vote: out-of-sample calibration and proper scoring; electoral power indices: coalition rules clearly specified. Publish none as validated without data and diagnostics.

## Quality profiles
- PR: Ruff, basedpyright in scoped strict all mode, pytest/Hypothesis, schema and source parity, browser smoke, security/tooling checks; deterministic short profile.
- Release: full integration, reference differential tests, repro assets, source-to-HF revision checks, mutation gates and profiling budgets.
- Scheduled: source drift, security history scans, property fuzzing, provenance verification, profiling trend. No repeated heavy jobs on every edit.

## Existing integration
`src/archive_govt_nz/domains/elections`; `spaces/nz-election-explorer`; `schemas/election`; `tools/check.py`; `conductor/tracks.md`; current `scripts/deploy_hf_space.py`. Avoid a second ETL, model registry, and new governance service.
