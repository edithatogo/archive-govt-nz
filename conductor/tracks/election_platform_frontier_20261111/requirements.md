# MoSCoW requirements and invariants

## Must
M-01 The source registry identifies publisher URL, legal licence, election year, source vintage, capture timestamp, content SHA-256 and data schema.
M-02 The presentation consumes a single validated release snapshot. A changed source cannot silently override a published model version.
M-03 Statutory Sainte-Laguë entitlement, 5% or electorate qualification, overhang, majority and excluded party votes pass independent fixtures and integer/property-based tests.
M-04 Public UI separates authoritative observed provisional/official, deterministic derived, probabilistic estimated, counterfactual and nonvalidated experimental results.
M-05 Code and CI use uv lock, Ruff select ALL (target-specific justified exclusions), basedpyright strict/all with measured diagnostics, Hypothesis, pytest, gremlins mutation and Scalene profiling. Keep heavy lanes bounded and scheduled/on-demand; no fake pass or suppressed failing stage.
M-06 Relevant source results are verified and snapshot version preserved before any publication; error fails closed and preserves previous good release.
M-07 Privacy/secrets and dependency scanning, least-privilege tokens, supply-chain hashes, reproducibility evidence, and action SHA pins are required. Existing scanning PR #860 is reconciled, not duplicated.
M-08 Release manifest includes source IDs, Gold dataset hashes, software revision, runtime/toolchain versions, published HF SHA, validation receipt and rollback pointer.
M-09 Zero human review bureaucracy for solo developer; automated green gates mandatory.

## Should
S-01 Geographic maps use versioned electorate boundaries with an independently checked change crosswalk.
S-02 Longitudinal series preserve comparable denominators, boundaries, party identifiers and election rules.
S-03 Simulate special-vote composition jointly, with calibration on prior elections, predictive uncertainty and prospective frozen forecasts before 27 November 2026.
S-04 Coalition feasibility, veto/pivotality and Shapley–Shubik/Banzhaf power calculations are correctly named and verified against independent reference algorithms.
S-05 Provide a shareable scenario URL, downloadable machine-readable scenario input and analysis receipt.
S-06 Downloadable research bundles contain CSV/Parquet/Arrow, CSL-JSON citations, figures, method definitions, source IDs and exact code revision; deterministic rerun parity.
S-07 Performance, memory and user latency budgets are measured under realistic corpus sizes and Android-class mobile clients.

## Could
C-01 Formal model checking of simplified statutory allocation invariants and optional zero-knowledge proof of source-to-result computation.
C-02 Party manifesto/Hansard/policy alignment with provenance and human-validated labels.
C-03 Agent-based bargaining, paignia-style game ontology mapping and experimental biological/quantum demonstrations behind explicit research-only boundaries.

## Won't (current production release)
W-01 Present speculative quantum/biological metaphors as empirical estimates.
W-02 Call a 2023 official-capture receipt an official 2026 election result.
W-03 Use arbitrary fixed election outcomes in production code or disable security/tests to force deployment.
W-04 Require multi-person approvals, Copilot, premium hosted services or enterprise governance machinery.
