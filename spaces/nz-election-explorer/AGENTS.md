# Election analytics: single-developer engineering contract

## Authority and publication rules
- Authoritative public returns are obtained from the NZ Electoral Commission. Separate election year, preliminary/official vintage, capture timestamp, release date and SHA-256 provenance.
- A provisional result is never called an official declaration. All deployed values must reconcile to one immutable published release fixture.
- Do not embed a second copy of result values in charts or UI; the Space loads `data/2026-preliminary.json` and fails closed on inconsistencies.
- Do not infer causal effects, forecast probabilities, electorates or special-vote margins from arbitrary illustrative numbers. Synthetic fixtures must be labelled `synthetic`.
- A 2026 official-data capture may only be admitted after the 27 November Commission release and verification.
- Show observed, derived, estimated, counterfactual, illustrative and experimental outputs in separate analytical strata.

## Harness / context engineering
- Start with `AGENTS.md`, `conductor/tracks.md`, the relevant election Conductor track and `schemas/election/`.
- Use test-first changes: a failing test for each known defect, a focused fix, then full relevant elections CI. Do not silently alter expected values to match invalid code.
- Reuse existing Pydantic contracts, DuckDB/Arrow/Parquet derivatives, provenance mechanisms and repository security workflows. Avoid parallel implementations.
- Pin all nontrivial production transformations to input fingerprint, code revision, computation version, model parameters and deterministic seed where applicable.
- Validate independent election reference fixtures and check that excluded parties contribute zero seats but nonzero party-vote shares to disproportionality indices.
- Keep Conductor requirements/design/implementation/evidence/limitations aligned, but avoid approval gates, reviewer assignments and multi-person ceremonies for a solo developer.
- PRs require: focused test result, full CI result, schema checks, vulnerability/secret checks, publication parity receipt and a rollback path.
- Do not claim a pass from GitHub Actions until GitHub reports success for the exact head SHA. Do not claim deployed parity until the Hugging Face serving revision and page are checked.
- Never introduce credentials into the repository or upload evidence containing secrets. Use OIDC/scoped tokens and read-only permissions except in the explicit deployment step.
- Prioritize build reproducibility and maintainability over novel tooling; experimental research belongs behind independently verified production surfaces.

## Next high-assurance improvements
1. Add an immutable source-download manifest and content hashes for the 2026 preliminary release; preserve the Commission HTML/CSV source.
2. Add statutory edge-case and tie-resolution fixtures, plus property-based tests for allocation conservation, eligibility and house expansion.
3. Add an offline HTML/JS browser smoke test (desktop/mobile, keyboard and screen reader semantics) and resource-budget checks.
4. Pin dependencies and GitHub Actions SHA; create an SBOM, run dependency review/CodeQL, and sign or attest immutable deployment artifacts.
5. Publish signed release evidence including dataset vintage, model versions, diff against previous revision and Hugging Face revision.
6. Triage existing privacy/security PR #860 separately; resolve conflicts rather than duplicating Presidio/Gitleaks controls.
7. Restore statistical research modules to the published interface only with independently reviewed empirical datasets, diagnostics and uncertainty.
