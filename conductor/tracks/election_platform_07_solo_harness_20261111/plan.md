# Executable delivery plan — 07_solo_harness

- [ ] Identify canonical source contracts, licences, baseline and evidence requirements.
- [ ] Add a failing focused regression/property test for the next implementable unit.
- [ ] Implement minimal correct source code reusing established archive contracts and Polars/Arrow/DuckDB where suitable.
- [ ] Verify independent fixtures, provenance, uncertainty and result-type classification.
- [ ] Run Ruff ALL, basedpyright maximal scoped strictness, pytest/Hypothesis and applicable mutation/security gates.
- [ ] Preserve profiling, performance, accessibility and citation artifacts as required.
- [ ] Confirm exact-head CI, publication bundle/Space parity, then close with auditable evidence.

## 22 November 2026 — bounded export-capture lint repair

The PR assurance lint stage exposed 42 existing findings in
`scripts/capture_datafinder_exports.py` and one annotation-only import in
`generate_vote_splitting_figures.py`. The repair is limited to those two source
files and offline regression tests; the checklist above remains open.

- Reuse the existing HTTPX dependency and archive URL guard. API credentials are
  accepted only for the approved Stats NZ HTTPS origin, API calls do not follow
  redirects, and every download hop after the first is unsigned and validated.
  Redirects have a finite bound, errors omit raw response bodies, and raw response
  streaming preserves the bytes passed to the CAS. Only the script's progress
  logger is enabled, so it does not enable HTTPX's signed-URL diagnostics.
- Resolve the remaining lint findings in code: executable script entry point,
  documentation, HTTP status names, UTC, imports, exception messages and progress
  logging. Move the figure's annotation-only import behind `TYPE_CHECKING`.
  No dependency, lint-policy, scientific acceptance or capture receipt changes.
- `.venv/bin/python -m pytest tests/capture/test_datafinder_exports.py -q`:
  **39 passed** under the existing CPython 3.15.2 environment. All HTTP traffic
  uses `MockTransport`; no credentials were read and no source capture occurred.
- Scoped `ruff check` and `ruff format --check` for the two source files and new
  test module passed. `basedpyright --threads 1 --pythonpath .venv/bin/python
  tests/capture/test_datafinder_exports.py` reported **0 errors, 0 warnings**;
  `git diff --check` passed.
- The initial `./scripts/test-focused.sh` invocation exited 2 because its exact
  CPython 3.15.1 guard rejects the existing 3.15.2 interpreter. The environment and
  guard were then preserved; the direct pytest result is scoped evidence, not a claim
  that the complete harness or hosted assurance gates passed.

## 22 November 2026 — bounded type-interface follow-up

One full harness attempt passed lock, Conductor state, format and lint, then its
four-worker type stage reported a worker `SIGKILL` and stalled. That owned run was
interrupted. The unchanged type command with one worker completed and identified
48 existing diagnostics in six files; the repair stays within those interfaces.

- Preserve the UMAP seed, parameters, MDS fallback and existing anchor values.
  Import `UMAP` from its defining module and require a genuine NumPy array with
  one two-dimensional row per electorate before indexing or mutation.
- Matplotlib 3.11.2's [documented scatter contract](https://matplotlib.org/stable/api/_as_gen/mpl_toolkits.mplot3d.axes3d.Axes3D.scatter.html)
  accepts array-like z coordinates; inference from the untyped default `0`
  incorrectly narrowed them to integers. Use a precise local callable protocol
  for those arguments and the verified `axis3d.Axis` type for 3D panes. Keep every
  plotted value and style argument, and import `Line2D` from its defining module.
- Wrap existing integer PowerPoint dimensions in native `Emu` values without
  changing their magnitudes, and pass the output path as `str`. Explicitly import
  `urllib.error` and annotate the existing capture-failure records as dictionaries.
  No new ignore, cast to `Any`, dependency change or acceptance-threshold change.
- The affected manifold test file passed **13 tests**, including eight new
  malformed-output, shape, fallback and anchor-preservation cases. The existing
  five-figure materialization test passed. These used the explicitly selected
  repository CPython 3.15.2 interpreter, before the guard alignment below.
- A synthetic before/after comparison produced **7 byte-identical PNGs**,
  identical contents for **all 93 PowerPoint package members**, and an identical
  manifold model. This is regression evidence, not scientific qualification.
- `uv run --locked basedpyright --threads 1` now reports **0 errors, 0 warnings**
  across the repository. Affected Ruff ALL, format checks and `git diff --check`
  pass. The one-worker run is diagnostic evidence; it does not replace the
  configured four-worker stage or claim a complete harness/hosted-CI pass. The
  full harness is reserved for the combined reviewable candidate.

## 22 November 2026 — focused-wrapper runtime alignment

The wrapper now reads the exact `.python-version` pin, currently **3.15.2**, and
the active `AGENTS.md` runtime contract agrees with that pin. It still rejects a
different patch version; isolated checks also confirm that a minor-only pin is
not accepted. `./scripts/test-focused.sh tests/capture/test_datafinder_exports.py
-q` now passes **39 tests**. Shell syntax validation passed. The environment,
authoritative pin and resource-gate configuration remain unchanged.

## 22 November 2026 — hosted runtime and registry follow-up

At PR head `e987d4121473d5d07b65f7a6f29753f361a36041`, the macOS configured
`basedpyright --threads 4` stage passed with zero diagnostics. All three OS jobs
reached the full pytest stage and failed on the same Parliament runtime guard and
Tobac URL inventory defects. macOS also lacked the OpenMP library required by the
locked XGBoost wheel. Its 9,088 passing tests, 13 failures and two collection
errors are partial run evidence, not full assurance acceptance.

- Align Parliament's exact runtime guard, actual continuation workflow selection,
  inline startup assertion and active hosted contract to the authoritative
  CPython 3.15.2 pin. Rejection of other patch/minor versions remains strict;
  schedule, workflow authority, capture bounds, concurrency and gate resources
  remain unchanged.
- Add only a conditional macOS setup step to install `libomp` and print its
  installed version. The [XGBoost shared-library documentation](https://xgboost.readthedocs.io/en/stable/build.html#building-the-shared-library)
  and [upstream macOS OpenMP discovery](https://github.com/dmlc/xgboost/blob/master/cmake/FindOpenMPMacOS.cmake)
  identify the Homebrew dependency; the completed job reported its absent
  `libomp.dylib`. Shell syntax is checked locally; native installation and import
  qualification remain for hosted macOS. No thread count, timeout, test scope,
  coverage floor or acceptance gate is relaxed.
- Reconcile the existing Tobac source set to all 61 canonical URLs while retaining
  manual scheduling and disabled publication. The deeper duplicate-identity check
  is resolved through an exact immutable pre-reconciliation registry snapshot and
  live-row consolidation, documented in
  [the owning Tobac plan](../tobac_sources_20261025/plan.md). Dated binding/capture
  bytes remain unchanged; version separation is not capture re-verification.
- `./scripts/test-focused.sh` across the six affected Parliament files, existing
  Tobac archive test, source-set contract/CLI tests and workflow-policy tests:
  **158 passed in 12.88s**. Four new cases reject different Python patch/minor
  versions before state access; the workflow regression binds runtime selection
  to `.python-version`. The existing retry-budget test now supplies an explicit
  mock HTTP transport, avoiding executor SOCKS initialization and rejecting any
  unintended request without changing its timing assertions or production code.
- Affected Ruff ALL and format checks passed. Scoped basedpyright on the five
  changed Python files reported **0 errors, 0 warnings**. Native source-set
  parsing and the actual Parliament startup-version assertion passed. Isolated
  mutations of snapshot bytes and current aliases were rejected by the existing
  integrity assertions. The historical binding hash remains
  `47c42a5384a88f58bda7af87b56a5e3c297d4afd7a9a04097ce48c24172a6fb2`.

Required hosted assurance must qualify the combined follow-up commit. No source
capture, operational dispatch, publication, deployment or remote mutation was
performed during this repair; historical evidence and unresolved source rights
and scientific qualifications remain intact.
