# Run Log

## Exact GDP quarterly source profile — 2026-08-31

- Required native `./scripts/validate.sh` at `41e7717` passed all gates:
  2,790 tests/75.20s/97.07%, eight existing cleanup warnings, 41 schemas/31
  samples, 9/9 parity, all mutation and supply-chain checks. Log SHA
  `cd0e89c8202eaaceca1bbff207ea5d46145512b68383901461c2abc8b1656656`.
  Only two reviewed timestamp-only generated files were restored afterwards.
- Exclusively retained `silver/raw-stats-gdp-20260831-v1`; all four files
  byte-identical to both pilots and original SHA unchanged. Source-specific
  output remains noncanonical and unpublished.

- Registered bounded Phase 5.1 task before implementation in independent clone.
  Red test failed collection on absent `gdp` module, exit 2. Focused suite
  subsequently passed 45 tests; module coverage 100% (90 statements/20 branches).
- Parent review corrected locale dependence and lineage omissions; tokens,
  scaling, number-format attribute and date-range dependencies now have tests.
  Ruff/typing pass; initial two test typing errors corrected, no gate weakened.
- `pytest tests/domains/health_appropriations/test_gdp.py --no-cov --gremlins
  --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/gdp.py
  --gremlin-workers=2 --gremlin-no-coverage-filter --gremlin-report=json
  --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 -q`
  passed: 37/37 killed, no survivors/errors/timeouts/pardons/cache hits, 36.11s.
  Report SHA `25b0cb80d474351f49ea7a7b58778489ba55b12bb6747b24c39fb1579dd90290`.
- Two local four-file pilots match; 60 facts/900 lineage/2,287 dispositions,
  85,176 bytes, all original cells and emitted fields independently reconciled.
  No source write, download, aggregation, denominator selection or publication.
- Existing Pharmac PR #295 observed externally merged with seven green checks;
  exact delivery receipt is in `gdp-profile.md`. No merge call by this agent.

## Planner main integration checkpoint — 2026-08-31

- Merged main `d6bc0c9` into the feature branch as `841bd5f`, preserving both
  sides of three track-record conflicts. The complete incoming evidence ledger
  remains an exact prefix followed by the planner event. Source/test hashes
  remain unchanged; 102 focused tests passed in 9.91 seconds, targeted typing
  passed, and Conductor validated 71 tracks. No second full harness is claimed.
- One `uv run ruff` launch failed to initialize the shared uv cache with
  `File exists`. Direct invocation of this clone's installed Ruff passed both
  format and lint checks. No shared cache repair or dependency change occurred.

## Additive inventory assurance checkpoint — 2026-08-31

- Functional commit `c6d0e37` adds the read-only planner and synthetic tests.
  Final critical run: 102 passed in 53.42 seconds; 100% line/branch coverage,
  120 statements and 20 branches. Report SHA-256:
  `1de80a359e4875a642d3bbfa27738159f416dc920830c2b814b1542f49c0ae1b`.
- Cold, unfiltered mutation used all 102 tests, one worker, the unchanged
  30-second timeout and zero allowed pardons, with no exclusions. All 78
  mutations were killed; zero survivors, timeouts, errors, pardons or cache
  hits. Exit zero in 567.73 seconds. Report SHA-256:
  `e04e4f3bf0d394d4cea336ab7cdb3a414af999f3aec6b396d38e1f1bf82869a5`.
- Final source SHA-256:
  `ee64c8cfd1ec90404d706986e3a8236383f90baefeb7e80bc8bee8b61ee07aac`;
  tests SHA-256:
  `aebb8238f66a21b2c85d267df2cb787807b6af80ebdba161f8e54c09e2f12559`.
  Ruff and targeted typing pass. Independent read-only review found no
  actionable issue within the reviewed-root, fixity/metadata-only contract.
- Required native command:
  `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4
  ./scripts/validate.sh`, CPython 3.14.6. Lock, Conductor (70 tracks), formatting
  (1389 files), lint and typing passed. The test stage collected 2284 tests
  with seed 2238017422, showed two failure markers and reached 97% plus further
  progress before the unchanged 300-second deadline ended the harness with
  exit 124. No traceback, final summary or coverage result was emitted.
  Failure identities are unknown; this is NOT a full-suite pass or a claim
  that the failures are unrelated. Post-test gates were not reached.
  Native log SHA-256:
  `b4d8c04ce220a9d2b25570b8e46c534f633733c511a5f3a574dea07ec11f4f0f`.
- No owned workers remain. Two generated timestamp-only legislation receipts
  were restored exactly. The stale lastfailed cache contains only the earlier
  replaced, unparameterized permutation-property node, not identities for
  this native run's failure markers. No heavy blind retry was made.
- A second live read-only call with final source bytes produced exactly the
  same inventory receipt hash as the first. Retained inputs/v4 bytes remain
  unchanged. Hosted validation and publication approval remain separate.

## Local additive inventory planner — 2026-08-31

- Work is isolated in a new standalone clone from `113bac5`, not a shared
  worktree or another actor's environment. No CLI or publication path is added.
- Red: `uv run --locked pytest -q
  tests/domains/health_appropriations/test_candidate_inventory.py --no-cov`
  exited 2 because the planner module did not exist (3.77 seconds).
- Initial implementation passed 15 tests. Expanded tests exposed a portable
  fixture distinction: `MANIFEST.JSON` aliases the manifest on case-insensitive
  filesystems and therefore fails fixity rather than the extra-file contract.
  Both rejection paths are asserted, not bypassed.
- The filesystem permutation property hit the unchanged Hypothesis 200 ms
  deadline once at 773.43 ms, then took 18.01 ms on replay. Replaced random
  filesystem permutations with all 24 explicit permutations, retaining a fast
  generated invalid-pin property that fails before filesystem access. No
  deadline, threshold or assertion was relaxed. Final focused run: 99 passed
  in 9.75 seconds; Ruff passes. Critical coverage/mutation and native assurance
  remain pending their coordinated resource slot.
- A read-only live call verified all 94 retained v4 entries (39,390,246 bytes)
  and the four explicitly pinned successor packages: 16 additional files,
  1,965,259 bytes, including unchanged package manifests. All four original
  hashes join exactly one complete capture row, v4 rights resource and v4
  original. Local inventory receipt SHA-256:
  `26102f7aa1ea2b4bce96ae9bf861d3838848d48606cd63bbc7ec19ad7fe86951`.
- Inventory status is not semantic validation, legal assessment, candidate
  creation or publication approval. Metadata overhead and a future root
  manifest are not planned. Zero replacement/deletion applies to proposed
  payload paths only. Older raw-run/compatibility/Gold/plot packages remain
  outside these four fixed profiles; no rights state or archive byte changed.
## Pharmac native assurance and archive retention — 2026-08-31

- Unchanged native harness at `677326a` passed all gates: 2,459 tests in
  145.43 seconds, 97.01% overall coverage, eight existing cleanup warnings.
  Task-owned uv cache, ctrace, JIT off and four pytest workers were used.
  Native log SHA-256 is
  `ea23b74dabb6a092e9d637eaa06d7bebddca959f01c703f2e519ba5cefb321f0`.
- Restored only the four reviewed timestamp-only outputs generated by this
  run; no source/test changes occurred during assurance.
- Exclusively created `silver/raw-pharmac-cpb-20260831-v1` and read back all
  four files against both existing pilots: 31,646 bytes, identical manifest
  `5eea323f1f9360fb7a92b7c2d9f92f1922dfb6f447a8252c8ca8b3ebf64ff248`.
  Originals and both pilots remain untouched. No network or publication.

## Pharmac preserved-HTML normalization — 2026-08-31

- Registered Phase 5.1 before source edits; functional checkpoint `d3ad31a`
  remains an in-progress task until required assurance and hosted delivery.
- Read the whole retained table and surrounding scope, not only preview rows.
  Reconciled exact census source `pharmac_cpb-010`; no source request occurred.
- Red pytest collection failed on the absent adapter. Full focused progression
  reached 69 tests, 100% critical line/branch coverage and passing Ruff/types.
  A wrong coverage module spelling produced no data; the corrected dotted
  name passed the unchanged threshold. Parent review's missing-lineage-null
  regression failed before its narrow correction and then passed.
- Two exclusive local pilot directories each contain four byte-identical files,
  31,646 bytes, manifest
  `5eea323f1f9360fb7a92b7c2d9f92f1922dfb6f447a8252c8ca8b3ebf64ff248`.
  Independent table parsing reconciled all 64 physical cells and 42 supplied
  numeric/missing values against fourteen facts and their amount lineage.
- Source remained byte-identical. Exact source and implementation boundaries,
  pending heavy gates and prior PR #285 hosted delivery are in
  [the CPB receipt](./pharmac-cpb.md).
- Cold mutation command used the complete focused file, `--gremlins`, exact
  `--gremlin-targets=src/archive_govt_nz/domains/health_appropriations/pharmac.py`,
  two workers, no coverage filter, JSON reporting and zero allowed pardons.
  All 93 mutants were killed in 172.27 seconds, with zero cache hits or other
  outcomes. The generated coverage fragment was retained outside the checkout
  before the full harness to avoid mixing instrumentation runs.

## Plot mutation recovery and hosted readback — 2026-08-31

- A coordinated retry in the standalone recovered clone retained the same
  renderer and tests, with one worker, a cold cache, unfiltered selection,
  unchanged 30-second mutant deadline and zero allowed pardons. The same
  21 unit/protocol tests passed; only the two previously documented full-PNG
  integrations were excluded. All 67 mutations were killed, with zero
  survivors, timeouts, errors, pardons or cache hits; exit zero in 710.55 seconds.
- Recovered report SHA-256:
  `45decbb57caf70129b04f78c88cd008b8d7ba6bc060c2f5c6a83fb44a13d365d`.
  Unchanged renderer SHA-256:
  `07674afbc970aed73a662e43a8c2450560d40e587524a86c2901fba835566df5`.
  The earlier 42-kill/25-timeout report remains preserved separately; this
  later result does not rewrite either native harness failure receipt.
- REST readback observed PR #274 merged at 2026-08-31T11:34:26Z as
  `4dacd12be50fcc221906db0e497e2073e7e7b0f7`, from tested head
  `4760cf2bedf54efc0ee209bcdb5903a353640495`. Main readback
  `113bac597cb95ce7aba5c877da4cffde6a0346cc` contains that merge.
  This agent did not perform the merge or rerun cancelled workflow lint.
- Lint run 33385763148 was first observed cancelled before any step ran,
  with GitHub attributing cancellation to `edithatogo`. A later REST readback
  at 11:49 UTC reports all seven head checks successful, including lint and
  Linux/Windows/macOS assurance. Current hosted success and the earlier
  cancellation are separate observations, not a claimed agent retry.
- No originals, retained derivative files or Hugging Face publication changed.

## Source plot context-style review fix — 2026-08-31

- Isolated worktree starts at merged plot commit `b149d37`; its own locked
  environment uses CPython 3.14.6 and uv 0.11.8, not another actor's `.venv`.
- Three new focused regression cases fail on the original renderer: one
  same-context year gap changes markers/colors, while two distinct contexts
  with colliding abbreviated labels lose a legend entry. Command:
  `uv run --locked pytest tests/domains/health_appropriations/test_plot_export.py
  -k 'disconnected_context or colliding_display' -q --no-cov`;
  exit 1, three failures and 20 deselected (40.62 seconds).
- Fix keys visual styles by canonical full context, retaining physical line
  breaks and disambiguating colliding display text with context ordinals.
  Source objects, existing derivatives and published bytes are untouched.
- First green run passed all 23 renderer tests (78.51 seconds). Ruff separately
  flagged a reassigned loop variable; using an explicit display-label variable
  resolved it without suppressions. Ruff format/check now pass.
- Isolated renderer coverage run passed all 23 tests (78.05 seconds), with
  100% line and branch coverage: 132 statements, 30 branches. Command used
  `COVERAGE_CORE=ctrace PYTHON_JIT=0 uv run --locked pytest
  tests/domains/health_appropriations/test_plot_export.py -q
  --cov=archive_govt_nz.domains.health_appropriations.plot_export --cov-branch
  --cov-report=term-missing --cov-report=json:coverage/plot-context-critical.json
  --cov-fail-under=100`.
- First mutation attempt used the documented selection excluding only
  `preflight_and_two_reproducible_builds` and
  `cli_preflight_render_and_redacted_failure`, with 21 selected tests,
  `--gremlin-workers=2 --gremlin-clear-cache --gremlin-no-coverage-filter`,
  zero allowed pardons and the unchanged timeout. It exited zero after
  1042.05 seconds but recorded 42 kills and 25 timeouts out of 67 mutants,
  zero survivors/errors/pardons/cache hits. This is incomplete mutation
  evidence, not 67 kills; the plugin's combined percentage is not repeated
  as a mutation-pass claim. Report SHA-256:
  `bcf99622a4e7339017896f5896b567de3246eb8653c064690b7146aa65de8b03`.
  Report and stranded coverage bytes were retained outside the checkout before
  subsequent coverage runs. Coordinated resource isolation precedes retry.
- A fresh CLI build consumed reviewed Gold manifest
  `ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`
  into a new temporary directory. `diff -qr` found all eight files identical
  to retained `raw-plots-20260831-v2`; both manifests hash to
  `a04b1b8785d7a4da67ad1b83d6449592838ed0359de792368bb8f150155786d2`.
  The command exited zero and retained inputs/outputs were not overwritten.
  Matplotlib 3.11.1, Pillow 12.3.0, FreeType 2.14.3 and Agg remain unchanged.
- The CLI launch emitted two uv interpreter-cache warnings (invalid MessagePack
  markers), then uv recreated this isolated environment as CPython 3.14.6.
  This is an observed runtime/cache event, not proof of the timeout cause;
  no source or dependency-lock modification was made to work around it.
- First native harness exited 1 at strict typing, before pytest: the new test
  treated Matplotlib `ArrayLike` as iterable and legend `Artist | None` handles
  as lines without narrowing (five diagnostics). Lock, Conductor (70 tracks),
  formatting (1364 files) and lint passed. This is a test-code defect, not an
  overload timeout; fix the assertions and rerun required validation.
- Type repair uses NumPy array equality and explicit `Line2D` runtime narrowing
  without casts, ignores or weakened value/style assertions. Targeted
  basedpyright reports zero errors/warnings; Ruff passes; all three regression
  cases pass (41.54 seconds). Production renderer bytes are unchanged.
- Corrected native retry used the same command and limits:
  `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4
  ./scripts/validate.sh`. Lock, Conductor (70 tracks), formatting (1364 files),
  lint and strict typing passed. Pytest collected 1913 tests with seed
  `3207899423`, reached 97% plus further progress, and displayed one `F` marker
  before the unchanged 300-second test-stage deadline ended the harness with
  exit 124. No traceback, final test summary or coverage result was emitted;
  the failure identity is unknown (the lastfailed cache is empty), not assumed
  unrelated. Post-test gates were not reached. This is NOT a full-suite pass.
- Only the two generated timestamp-only legislation receipt diffs were restored
  in this owned worktree. Process inspection found no residual owned pytest
  processes. No further heavy local retry is attempted under the observed host
  contention; the scoped PR will expose these limits and require exact-head
  hosted validation before any merge decision.
- Functional change and paired evidence were committed/pushed as `0c78b4c`,
  PR #274. GitHub reported documentation conflicts with main, so checks did
  not start. Before integration, this agent observed its worktree, registration
  and local branch disappear; it performed no removal. The pushed commit and
  external validation artifacts remained available, with no uncommitted work
  outstanding. A standalone `--no-hardlinks` temporary clone was recovered from
  the repository without modifying its original checkout and then pointed to
  GitHub. It is not registered in the original worktree list.
- Integrated exact main `d0a36f1099fce30427927ebda4f735c3c9617a5a` into the
  recovered feature branch. Four documentation append conflicts retain both
  branches' records; main's complete evidence ledger remains a byte prefix,
  followed by this correction's observations. Renderer SHA-256 remains
  `07674afbc970aed73a662e43a8c2450560d40e587524a86c2901fba835566df5`.
  No original data or publication changed; no PR merge was performed.
- Post-integration checks pass: 23 renderer tests (54.49 seconds), Ruff
  format/lint, targeted strict typing and Conductor (70 tracks). The complete
  incoming ledger prefix and original legacy prefix both verify. No full or
  mutation rerun was performed after recovery; their earlier limitations are
  not retroactively converted into passes. Hosted checks remain pending.
## Budget hosted delivery and validation recovery — 2026-08-31 UTC

- PR #273 observed merged at 10:59:47Z as `d0a36f1`, seven exact-head checks
  successful; hosted Ubuntu passes 1,972 tests, eight warnings, native gates
  and 112-component SBOM. Reader source/tests are unchanged at merge.
- An active worktree/interpreter disappeared during the subsequent local
  mutation run: 27 kills, 83 errors, exit 1. Its report is preserved; no cleanup
  was performed by this task and no implementation was lost from pushed Git.
- Recovered into an independent no-hardlinks clone outside the shared worktree
  registry. Fresh cold/unfiltered mutation passes 110/110 kills, no survivors,
  timeouts, errors, pardons or cache hits. Detailed hashes and boundaries are
  in `raw-budget-successors.md`; no originals/publications changed.

## Budget successor consumer — 2026-08-31 UTC

- Budget 2026 remains a separate immutable source vintage. Two local builds
  match; independent OOXML reconciliation and final verified-package readback
  account for 185 facts, 3,145 lineage entries and all 6,451 input rows.
- Reader implementation `07029cc` plus independent corruption fixtures passes
  61 focused tests at 100% critical coverage on CPython 3.14.6. Strict integer
  count rejection was added after red tests exposed bool/float equality.
- Native validation passes pre-test gates but exits 124 at its unchanged
  300-second test-stage deadline after 100% progress on 1,972 items. No final
  summary or overall coverage was received; no full-pass claim is made.
  Detailed receipt and remaining assurance gates: `raw-budget-successors.md`.
- PR #270 is now observed merged with seven successful exact-head checks and
  identical head/merge trees. This closes bounded donor conformance delivery,
  not the broader assimilation track. No originals or publications changed.

## Source plot hosted delivery — 2026-08-31 UTC

- Integrated full native harness passes on `62dc6e4`, after main's extra CLI
  coverage/dependency changes: 1,911 tests collected, test gate exits zero,
  96.75% overall coverage, 100% across Health-domain production modules,
  40 schemas/30 documents, 70 tracks, 9/9 parity, all native mutation and
  supply-chain gates, 111-component SBOM. CAS 288.53 MB/s versus 25.0 minimum.
  Unrelated timestamp-only generated evidence restored after completion.

- PR #269 merged `b149d3725165b4d4116e17452955c5602ac40ec4` at
  05:52:48 UTC after all seven checks passed on exact head
  `4f405e2abfba2444b8906412a65f7c128a269a13`, CI run `33361422682`.
  Health source/tests are unchanged at merge; whole trees differ because of
  unrelated main additions. No archive or publication bytes changed.
- Integrated that exact main into conformance. Squash-history conflicts were
  limited to Health track bookkeeping; retained incoming plot evidence and
  newer conformance evidence. Verified immutable evidence prefix unchanged.

## Donor failure conformance — 2026-08-31 UTC

- `4454d75` records full compile observations and maps donor semantic/failure
  risks to replacement tests. A synthetic duplicate-if script remains in CAS
  while receiver orchestration selects only its four source profiles. All
  253 selected tests and focused format/lint/types pass; no production changes.
- Final native harness exits zero: 1,907 tests, 96.48% coverage, eight existing
  SQLite warnings, 40 schemas/30 documents, 70 tracks, 9/9 parity, all native
  mutation/supply-chain gates, 111-component SBOM. CAS 586.10 MB/s versus the
  unchanged 25.0 minimum. Same runtime controls as the source plot harness.
- CLI verification of raw manifest `da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`
  passes without creating new state. This is readback, not a new extraction.
  Timestamp-only unrelated generated evidence was restored after validation.
- No raw/HF bytes or donor retirement changed. Next separate pilot: captured
  Budget 2026 headers match the supported 17-column contract. Captured HLFS
  working-age population is not silently accepted as total population for
  health spending per capita; M-12 denominator selection remains open.

## Source plot contracts — 2026-08-31 UTC

- Final post-preflight-fix harness exits zero for `eeb6200`: 1,906 tests,
  96.48% coverage, eight SQLite warnings, 40 schemas/30 documents, 70 tracks,
  9/9 parity, all native mutation and supply-chain gates, 111 SBOM components.
  CAS throughput 391.42 MB/s exceeds unchanged 25.0 minimum. Same runtime
  controls as below; no gate/deadline was weakened. Timestamp-only unrelated
  generated evidence was restored after completion.
- Final renderer mutation: 58/58 killed, zero survivors/timeouts/pardons,
  cold cache, no coverage filtering; 18 unit/protocol tests and two excluded
  full-PNG integrations, both retained in normal tests. Report SHA-256
  `2a0a3be0f3f91d9fd39268510109e967969310f7ed499f64e3bd9482d3c9fb72`.
  Together with unchanged reader/contract evidence, 128 current mutants killed.
  All 48 focused tests pass at 100% critical coverage. Third independent plot
  build after the fix matches all eight retained V2 files.
- Fresh donor-manifest and all 23 object hashes pass. Read-only full bytecode
  compilation of three pinned scripts confirms inspection/analysis compile,
  processor IndentationError line 199 offset 9. No imports or execution,
  source mutation, publication or donor retirement occurred.

- Full pre-review-fix harness completed successfully: 1,904 tests, 96.48%
  overall coverage, eight existing SQLite resource warnings, 40 schemas/30
  documents, 70 Conductor tracks, 9/9 parity, all native mutation gates,
  audit/licence/secret checks and 111-component SBOM. Command environment:
  `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4` with
  `./scripts/validate.sh`. Plot contracts/renderer killed all 83 selected
  mutants (test selection as below), report
  `08ad874967fcce964899fcf243e4e9860de31b508d374d77770492b2a0dd5121`.
- Review found that dry-run checked Gold integrity but did not enforce the
  point/series limits until actual rendering. Add red tests for both limits,
  share the check with dry-run, and revalidate; the successful harness above
  is evidence for the pre-fix code, not an automatic pass for later changes.

- Reader mutation: 44/44 killed, zero survivors/timeouts/pardons, coverage
  filtering disabled, two workers. Report
  `bddf14e38306e763243a087be53ac0b11152f9d5e2a8a99ee4bf65c692c948bb`.
- Full renderer tests passed (17 tests, 35.87 seconds), exceeding the mutation
  worker's fixed 30-second per-mutant subprocess limit. Retain both full PNG
  integration tests in normal validation. For renderer mutation only, use
  16 unit/protocol tests (100% line/branch, 12.52 seconds), excluding the two
  full six-PNG/CLI integrations. Transaction tests stub only PNG encoding in a
  scoped patch; the real writer is restored and explicitly exercised twice,
  including ambient settings. All mutants remain selected; disclose this test
  selection rather than calling it an unfiltered full-suite mutation run.

- First retained plot build and independent build agree on all output hashes;
  53 nominal, 48 growth, 53 GDP-share, four breakdown and six observations per
  recent classification. Growth omits five reason-coded comparisons. Original
  Gold manifest remains `ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`.
- Visual QA of all six PNGs found crowded growth year labels, categorical
  compression of omitted years, low-contrast hatch strokes and insufficient
  visibility for two very small breakdown values. Preserve `raw-plots-20260831-v1`
  as a QA build. Add regression contracts, correct rendering, and create a new
  version rather than overwriting it. V1 is not the final visual-QA pass.

- Gold reader began with a missing-module red test; 22 focused tests pass at
  100% line/branch coverage. Renderer began red, then 10 tests passed with
  97.83% critical coverage: the uncovered resource-limit rejection still needs
  explicit boundary tests. Lint identified formatting/import corrections.
  Added an ambient-Matplotlib-settings determinism test before fixing export
  isolation. No final renderer assurance claim yet.

- Exact-membership and JSON-policy strengthening kills all 26 unfiltered
  mutants with one worker, zero survivors/timeouts/pardons; report
  `0c4d98f6a288be8a590861adce990c534a329e8031e507c5a62b58a276733aab`.
  This precedes the sparse-period rendering adjustment below.
- Visualization skill review: recent classifications have only six source
  years, including Actuals/Estimated Actual/Main Estimates. Use discrete
  grouped bars for those two legacy-named trend images rather than implying a
  continuous trend; preserve inputs, source labels, units and amount types.
- Gold PR #261 conflict resolved at `ff99002`; 38 schemas/28 documents pass.
  Hosted Windows job `99373648468` failed only the existing CAS speed gate:
  14.74 MB/s versus 15.0 MB/s, 1 failed/1772 passed, coverage 96.28%.
  macOS assurance passed. Diagnose as runner-throughput variability, not a
  Gold assertion failure; one unchanged failed-job rerun is the bounded next
  route. Do not lower the threshold or claim the failed run passed.

- Began with a missing-module red test; five semantic tests now pass with
  100% line/branch coverage. First unfiltered one-worker mutation check killed
  21/26 mutants; five survived (JSON policy and segment membership), report
  `12154c17d7cd08963998f76bdfad15651503603e064fb624c6c6e30ab8a3d9a7`.
  Strengthen exact segment-membership and serialization contracts before
  claiming mutation completion. Lint also identified one long line to format.
- Gold draft PR #261 has no runs because it conflicts with intervening main
  `a17b0fd` (FOI attachment schema registration); reconcile both registrations
  without changing FOI code. No hosted pass or plot rendering claimed.

## Gold hosted assurance and main reconciliation — 2026-08-31 UTC

- Draft PR #261: `ff990026c793156c5bf651c2bc8c0c605bf881be` passed all seven
  exact-head checks. Windows attempt 1 failed only the existing CAS throughput
  check (14.74 MB/s vs 15.0; 1772 tests passed). An unchanged bounded failed-job
  rerun passed, job `99381611460`, run `33354394002`; no threshold was lowered.
  The earlier failed local and hosted attempts remain failures, not passes.
- Before merge, main advanced through FOI PRs #262/#264 to `78cd8fa`, creating
  another schema-list conflict. Retain both registrations and place Gold beside
  the existing Health schemas, reducing contention at the list head. Require
  fresh exact-head checks after this integration; the earlier green head alone
  does not authorize merging an untested new head. Plots remain separate work.

## Verified Gold persistence — 2026-08-30 UTC

- Functional commit `b38069c`, review fix `0d864d4`: 46 focused tests at
  100% critical coverage. Post-fix mutation reports 63 kills and 16 timeouts,
  not 79 verified kills (zero survivors/pardons), report
  `63eb5293fdbabfb980c7fb0551094a9ba3808110099c41f217cd207a68b4da65`.
  Preserve this report separately before any bounded retry.
- Four independently generated Gold packages match all eight files, including
  the post-review build. Manifest remains
  `ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`.
  Current-main schema checks pass 37 schemas/27 documents; Conductor 69 tracks.
  Prepare a draft PR with local limitations explicit and require independent
  hosted assurance before completion/merge. No local whole-suite pass claimed.

- The first full run ended with 1,669 passing tests and one Hypothesis input
  generation health-check failure in the unrelated discovery metamorphic test:
  six valid inputs in 1.15 seconds, seed
  `29426792313867042829794198730848378331`. Coverage was 96.12%, eight existing
  SQLite warnings. This is not a passing full harness; preserve the failure
  and replay its seed without suppressing any health check.
- Exact-seed single-process replay passed unchanged in 2.71 seconds. Keep the
  discovery strategy and health checks unchanged; rerun the complete harness
  with reduced xdist worker concurrency after integrating current main.
- Analytical PR #257 merged at `bc7949e92ff0fb7b31cdd389d325901ca7c19796`
  after seven exact-head checks passed. The merged tree includes intervening
  FOI-package changes, so it is not identical to the analytical head tree.
  Integrate that main state and rerun full validation before Gold delivery.
- Main integration retained both Gold and FOI package schema registrations;
  locked sync includes main's warcio dependency. No health-domain or health-track
  difference exists between the reviewed analytical head and its merged commit;
  the whole-tree difference is the intervening FOI work. The retry uses
  `PYTEST_XDIST_AUTO_NUM_WORKERS=2 ./scripts/validate.sh` with unchanged gates.
- The two-worker retry reached 98% without reported assertion failures but hit
  the existing 300-second per-stage timeout (exit 124). No surviving worktree
  test processes were observed. A third full attempt uses four workers to
  balance generation contention and the unchanged timeout; no gate is disabled.
- The third full attempt also timed out at 300 seconds (exit 124), after
  reporting several failures but before emitting tracebacks. Do not infer
  their cause from the earlier generation health check. Stop blind full-harness
  retries; use a fail-fast diagnostic run to capture the first actual traceback.
- The initial diagnostic incorrectly cleared configured pytest addopts, causing
  a test_verifier import-name collision during collection. That diagnostic is
  invalid evidence of a product failure. Preserve configured import behavior
  for its bounded correction; do not delete caches or rename unrelated tests.
- Corrected fail-fast diagnosis captured an unrelated legislation property
  timing failure: 278.29 ms initially versus 0.07 ms on replay, against an
  unchanged 200 ms Hypothesis deadline; 1,196 tests passed before stopping.
  This supports local scheduling/timing instability, not a deterministic
  legislation or Gold assertion failure. Do not disable deadlines or patch
  unrelated algorithms. Use independent hosted assurance after the in-scope
  provenance review fix, preserving local failure receipts explicitly.
- Detailed legacy readback identifies the discontinuous growth calculation:
  2020 was compared with 2000; the restored source series compares with 2019.
  The other guarded overlap is the 1997 accounting-basis change; 1972 is the
  initial observation in both. Old derivatives remain preserved, not rewritten.

- Extracted the tested bounded reader/lineage checks so compatibility and Gold
  consume the same verified raw snapshots. Moved the synthetic raw-run fixture
  into a shared conftest and preserved all 28 compatibility checks.
- Missing-reader and missing-Gold-module tests failed before implementation.
  CLI and schema tests then failed on missing API/file. Five malformed canonical
  identity cases failed to raise; the shared reader now rejects them. Formatter,
  lint and test typing were corrected before final focused checks.
- All 42 focused tests pass at 100% critical line/branch coverage across the
  reader and both exporters; 79/79 unfiltered mutants killed, zero pardons.
  Mutation report and policies are linked from raw-gold. A stranded coverage
  file was moved recoverably outside the isolated worktree before full coverage.
- Three live eight-file Gold builds match, including a post-mutation rebuild;
  independent readback checks hashes, schema, 321 input IDs and 4,798 lineage
  rows. Refactored SQLite output matches all four retained files byte for byte.
  Legacy analytical comparisons disclose float tolerance, restored years and
  gap/basis differences explicitly; donor original hash is unchanged.
- Full repository harness running. Source files remain unchanged during it.
  No new HF bytes, scheduling activation or donor-retirement action.

## Pure source-derived analytics — 2026-08-30 UTC

- PR #254 merged at `4e4586ec2b3732367c4ff8732957b6d40126e0e2` after all
  six exact-head checks passed. Hosted/tested trees both equal
  `1f983d17cfc44e877bed8c19e1d7fd505083058a`. Continued on
  `codex/health-source-analytics` in the isolated worktree. Original concurrent
  worktrees were not modified.
- Initial historical/Budget tests failed collection on missing modules.
  Historical negative cases exposed two fixture argument collisions, corrected.
  Two semantic tests then failed because non-month-end dates and non-text bases
  were accepted; validation now rejects both. Lint/types corrected before mutation.
- Historical 47 and Budget 32 tests pass at 100% critical line/branch coverage;
  30 generated growth cases pass. Unfiltered mutation kills 71/71 historical
  and 33/33 Budget mutants, zero pardons. See raw-analytics for report hashes.
- Verified retained raw-run snapshot computation accounts for 53 historical
  rows, 48 growth comparisons, 53 GDP denominators and all 215 appropriation IDs
  across 16 trend/four breakdown groups. Run verified before/after; no source
  or publication writes.
- Stranded mutation coverage file moved recoverably outside the worktree before
  full validation. Full harness exited zero: 1,656 tests, 96.09% coverage,
  eight existing SQLite resource warnings, 35 schemas/25 documents, 9/9 parity,
  all mutation and supply-chain gates; SBOM 110 components. Functional commit
  `0bf14b0`. No persistence or complete analytical-task claim.

## Persistent raw compatibility export — 2026-08-30 UTC

- Functional commit `e91d24b`: final isolated `./scripts/validate.sh`
  exited zero. All 1,577 tests passed at 96.05% coverage, with eight existing
  SQLite resource warnings; 69 Conductor tracks, 35 schemas/25 documents,
  9/9 parity, all mutation and supply-chain gates passed; SBOM 110 components.
  Only generated unrelated timestamp churn was restored in this worktree.

- A subsequent lint pass caught a formatter-moved annotation on that test
  double. Replaced the annotation with an object-accepting DB-API signature
  and a test-only cast. Standalone lint and test typing now both pass before
  the full harness is restarted.
- Two live exports match all four files byte for byte. The manifest is
  `fb405a2fdbb2809093cb03d62ddbe1fcb1a1f6f91d304666e8ef0964813f73fb`.
  Read-only schema/multiset comparison retains all 312 donor rows and adds
  29 historical Health observations; donor hash is unchanged before/after.
  The output contains all 341 facts, 4,918 lineage rows and 15 explicit binary
  representation flags. The 1976 source-token difference remains in exact
  sidecars even where SQLite REAL agrees with the donor value.
- Corrected unfiltered mutation run: 52/52 killed, zero pardons, report
  `5dd74daa8824b3e4b4e3b6230251190ec0b41a69e2aa218aa12e5d9e6a53801d`.
  Stranded mutation coverage files were moved recoverably to the temporary
  verification directory, outside this worktree, before full coverage.

- The first isolated full harness stopped at test typing: variable tuple
  indexing could include the manifest string, and the SQLite test double had
  narrowed the base execute signature. Corrected both test annotations/paths;
  production behavior and retained export bytes are unchanged. Full validation
  is rerun rather than treating focused production typing as the whole gate.

- Hardening expanded to 28 passing tests with 100% critical line/branch
  coverage, including 30 generated exact-amount lineage cases. CLI and schema
  were added after observed missing-entrypoint/missing-schema failures. A
  malformed integer coordinate red test drove explicit text validation.
- The first mutation attempt exposed test isolation failure: monkeypatching
  the shared SQLite connector intercepted coverage's `check_same_thread`
  connection. That run is invalid mutation evidence. The correction is to
  mock only the export module's SQLite reference before rerunning the gate.

- Resumed the existing task from `0d8e224`; initial full harness exited zero
  (1,508 tests, 95.97% coverage, eight warnings, all supply-chain gates).
  During that run, two additional validation processes were observed using
  the same checkout. Those processes and generated files were left untouched;
  this shared-checkout result is not the final isolated validation evidence.
- Created `archive-govt-nz-health-export` on `codex/health-persistent-export`,
  preserving the original branch. Merged observed main `97ae606` without
  conflict, installed the locked environment, and validated all 69 Conductor
  tracks with no errors. The historical evidence prefix is unchanged.
- Added six failing export contracts; import failed because the module did
  not exist. All six then passed after implementing verified snapshots,
  source/amount lineage checks, exclusive outputs and redacted failure receipts.
  Hardening and full isolated validation remain in progress.

## Raw compatibility projection — 2026-08-30

- Functional commit `42cee7dd159a9593ecfe243c3328b2756758165d`.
  Final full harness exited zero: 1,508 tests, 95.97% coverage, seven pytest
  warnings and an additional SQLite ResourceWarning during collection,
  33 schemas/23 documents, 9/9 parity, all mutation/supply-chain gates and
  110-component SBOM. Only unrelated generated timestamp churn was restored.

- PR #245 independently confirmed merged at
  `32fbbe391a169d00d760a051c39c9793a95f9109`, tested head
  `7388e32fb15ebc5373309bf86aa5e6927df87640`, all seven checks successful.
  Both trees equal `4b8cae1b1c229d1eace00b375f5c6a60a81d4dd3`.
  Re-anchored the uncommitted follow-on onto the identical merged tree with
  expected-OID guards; removed only its verified merged predecessor refs.

- Started the five-table raw-source compatibility task on
  `codex/health-raw-compatibility`. Initial tests failed on the missing module.
  The first 20 passed but critical coverage was 93.10%; added overflow, missing
  text, exact-boundary and source-immutability contracts, reaching 27 tests
  and 100% line/branch coverage. Lint and types pass.
- An initial coverage-filtered mutation run reported 14 survivors out of 35.
  Repeated explicitly without coverage filtering: all 35 killed, no pardons,
  report SHA-256 `1aefbe93868f64b328a174eb97ae8b424686d4e8bc73008fa69633949a25f8e3`.
  Filtered test selection is not used as final mutation evidence.
- Live read-only projection of the verified raw run yields 215 appropriations,
  ten BEFU, ten HYEFU, 53 historical Health and 53 GDP rows. Fifteen historical
  Health decimal amounts differ from their exact binary REAL representation;
  these representation flags are distinct from the one source/donor precision
  discrepancy. All exact amounts and context remain available in sidecars.
  No database or archive output was written. Export persistence remains pending.

## Typed workbook inspection — 2026-08-30

- Functional commit `446a82da14c0f3432298aef633841992cf7017b6`.
  Final full harness exited zero, including mutation and supply-chain gates
  and a 110-component SBOM. Forty focused unfiltered mutants were killed with
  no pardons. Only unrelated generated timestamp churn was restored.
- PR #243 independently confirmed merged at
  `d85c810ebc272163341e6517dd541a4cf3ee1dbd`, tested head
  `eac467d03dd07385e35cc2f105cc4571fecb8190`, all seven checks successful.
  Both trees equal `74eceb84762f147cf5fe81a13f02577bf2e98577`.
  Re-anchored the uncommitted inspector onto that identical tree using guarded
  refs; removed only the merged local branch and absent hosted tracking ref.

- Continued on `codex/health-workbook-inspection` from the validated read-only
  verification head while PR #243 awaits hosted checks. Baseline full harness
  before inspection code: 1,459 tests, 95.92% coverage, all gates passed.
- Initial tests failed with the missing inspection module; the first eight
  tests then passed. Listing-only and preview-byte-budget contracts failed
  before implementation. Added aggregate exact-boundary and CLI contracts.
- A first nonfinite fixture used `NaN`, which the workbook parser already
  rejects, invalidating the fixture's listing expectation. Corrected it to
  `1e309`: the expected red test showed an overflowed decoded preview was
  accepted. Strict JSON now rejects nonfinite previews; listing still works.
- Review found array/data-table formula objects were stringified to object
  representations. Two red tests reproduced the loss of useful fields.
  Structured attributes/text now survive; temporal displays are stable and
  unknown object types fail closed rather than leaking object representations.
- Twenty-two tests pass with 100% critical line/branch coverage, including
  30 generated head-dimension cases. Lint/types pass; 33 schemas and 23
  representative documents validate.
- Live typed CLI lists all eight original Budget sheets and returns 34 cells
  for two Raw Data rows and all 17 columns. The original hash remains
  `d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338`.

## Read-only raw-run verification — 2026-08-30

- Functional commit `d25fd8db6c760ef7dab4ae5be032f4f779e300e6`.
  Final full harness exited zero: 1,459 tests, 95.92% coverage, eight warnings,
  32 schemas/22 documents, 9/9 parity, all mutation/supply-chain gates and
  110-component SBOM. Only unrelated timestamp churn was restored.
- Re-anchored the in-progress branch onto the exact identical PR #242 merged
  tree with expected-OID guards, then removed its verified merged local branch
  and stale remote-tracking ref. The hosted branch was already absent.

- Continued on `codex/health-readonly-verification`, using the just-passed
  1,452-test full harness as the unchanged-code baseline. Added red library
  and CLI import contracts before implementing either surface.
- Initial focused coverage was 97.53%; four missing lines were symlink and
  late manifest-pin rejection. Added negative tests rather than lowering the
  100% gate. The 63-test focused/CLI/MCP suite now passes at 100% critical
  line/branch coverage; static checks pass.
- Live CLI and MCP both verify the retained 18-file run against manifest
  `da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
  Both return the same receipt. No rebuild or file creation is called.
- PR #242 independently confirmed merged at
  `f116967c627ed7d0e25deca893568921316a2661`, tested head
  `56d91b247963a6192b0567fad1f5629b891d64a0`, all seven checks successful.
  Both trees equal `3993fe88b7b173fb3a2916ae648cfd2b8f956d38`.

## Original-workbook orchestration — 2026-08-30

- Functional commit `578235c`. Final full harness exited zero: 1,452 tests,
  95.91% coverage, 32 schemas/22 representative documents, 9/9 parity, all
  mutation and supply-chain gates, 110-component SBOM. Three pytest warnings
  and five additional SQLite ResourceWarnings remain visible. Restored only
  unrelated timestamp churn. All 74 final unfiltered mutants were killed.

- Live preflight and the four-stage CLI build passed. Independent outputs
  match all 18 files byte for byte; complete-run reuse reverified source CAS
  objects and all output hashes. The run contains 341 facts: 215 Budget,
  ten BEFU, ten HYEFU and 106 historical, with no rejected selected values.
- The first 37-test mutation run killed 73/73. Review added two red contracts
  (duplicate JSON keys and absent completion schema), followed by a red
  unexpected RuntimeError contract. Corrected duplicate-key parsing, added the
  schema and used a narrowly annotated redacted adapter exception boundary.
  Errors are re-raised, not swallowed. Forty-one tests now pass at 100% line
  and branch coverage, including 20 generated derivative-corruption examples.
- Live run manifest SHA-256:
  `da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269`.
  Retained under `silver/raw-orchestrated-20260830-v1`. Observation context
  `2026-08-30T08:58:00Z` is local verification, not new HTTP capture.

- Continued the same track on `codex/health-raw-orchestration` while PR #232
  ran its immutable-head hosted checks. Baseline is the just-passed 1,411-test
  full harness before any orchestration source changes.
- The initial three tests failed collection with missing `rebuild` import
  (exit 2), then passed. Added corruption, path, schema, partial-run, identity
  and CLI contracts: 37 tests pass with 100% critical line/branch coverage.
- PR #232 independently confirmed merged at
  `08cfbab58b26495d39aa7903db0432c5b9a6669f`, tested head
  `fda419730cdff07235e951589ab44f5aa2a05626`, all eight checks successful.
  Both trees equal `f474597cc95d327d461dfcf5edc065aa0a2549a9`.
  Re-anchored this uncommitted next slice onto the identical merged tree using
  expected-OID ref updates; no source/index changes or rebase conflict.
  Removed the merged local branch only after verifying hosted deletion.
- Initial lint findings were formatting, explicit error-message variables,
  import placement and keyword-only CLI arguments. Corrected rather than
  relaxing gates. Type checks pass; final mutation/live/full checks follow.

## Historical final local gates — 2026-08-30

- Functional commit: `3376695b32021238e8e3152ae30188c9f38a5ca4`.
- Final full harness exited zero: 1,411 tests, 95.84% coverage, eight warnings,
  31 schemas, 21 representative documents, 9/9 differential parity, all
  mutation lanes, audit, licences, tracked secret scan and 110-component SBOM.
- Both new modules have 100% line/branch coverage (65 focused tests; 226
  domain tests). All 99 explicitly unfiltered mutations killed, no pardons.
- Independently rebuilt extraction and reconciliation outputs were retained
  outside Git; originals rehashed unchanged. See `raw-historical.md`.
- A concurrent task switched the shared checkout to main during validation.
  The local functional commit was transferred to its intended branch using
  expected-OID ref updates. Main returned to its prior commit; the other
  task's FOI worktree was not touched. No remote main write occurred.
- Hosted checks and merge remain separate. Continue with operational raw
  orchestration after delivery; this is not full assimilation completion.

## 2026-08-30 — Historical source continuation

- Reverified PR #230 as merged at `5eda36d`, with tested head `1619a6d`.
  The clean primary checkout is the sole worktree. Continued this same track
  on `codex/health-historical-extraction`; baseline full validation precedes
  source/test changes.
- The next source contains 53 Health and 53 GDP annual rows. Its donor Health
  table contains only 24 rows. Exact XML tokens, annotation markers, accounting
  transitions and March/June context must survive extraction; display formats
  cannot be used as a rounding rule for canonical facts.
- Baseline full harness exited zero: 1,346 tests, 95.72% coverage, eight SQLite
  ResourceWarnings and all schema, parity, mutation and supply-chain gates.
- Initial historical test collection failed as expected with missing module
  (exit 2); the first implementation passed 16 tests. Refactored row selection,
  period state, numeric checks and fact construction after static review.
  Added exact lexical decimals, guarded DTD rejection, parser ambiguity and
  negative-path contracts. Forty-three tests passed at 100% line/branch coverage.
- The first mutation run passed 46 tests, killed 69/70 mutations and selected
  an unrelated empty-series test for the surviving precision-rejection return.
  Re-running with explicit `--gremlin-no-coverage-filter` tests every mutation
  against the full focused suite; the first run is not a clean mutation gate.
- Two live builds of the original fiscal workbook yielded 106 facts, 1,143
  field-lineage rows and 1,503 cell dispositions, with zero rejected amounts.
  Both manifests and every output file are byte-identical. All 53 GDP values
  match the donor. Health restores 29 annotated years absent from its 24-row
  table and retains the exact 1976 token `605.70000000000005` rather than the
  donor's `605.7`. No original or published artifact changed.

- Forecast implementation commit: `801783d5069456ee16a1e1ce18a57c86a682bc9f`.
  Final `./scripts/validate.sh` exited zero: 1,346 tests, 95.72% coverage,
  eight SQLite ResourceWarnings, 30 schemas, 20 representative documents,
  9/9 parity, all mutation lanes, hygiene, CAS benchmark (281.03 MB/s), audit,
  licences, secret scan and validated 110-component SBOM. Restored only
  unrelated timestamp-only harness churn. Hosted CI/merge remain separate.

## 2026-08-30 — Forecast extraction continuation

- Prior goal turn made verified progress: PR #229 merged at `51ceeba` with an
  exact tree match to its tested head `069d297`. The clean primary worktree is
  the only worktree. Removed the local merged branch with an expected-OID
  guard. The leased remote deletion was rejected as stale; a read-only
  `ls-remote` confirmed GitHub had already removed it, so no deletion was
  retried. Source history remains recoverable through main and PR #229.
- Selected the next raw-source task on `codex/health-forecast-extraction`.
  Baseline production tests completed before new source/test edits; no shared
  coverage commands overlap. The new forecast test collected with the expected
  ModuleNotFoundError for the absent extractor (exit 2).
- Captured a synthetic Budget fixture and its existing output hashes before
  extracting shared integrity helpers. This is a refactor-parity oracle, not
  an original government payload committed to Git.
- Baseline full harness exited zero: 1,296 tests, 95.66% coverage and all
  schema/parity/mutation/supply-chain gates, including a 110-component SBOM.
- First implementation passed 83 tests. Static analysis identified nullable
  workbook-library coordinate annotations; explicit coordinate decoding fixed
  the mismatch. Remaining Ruff findings were import/pairwise/annotation style,
  not suppressed failures. The next 89-test run had 100% line/branch coverage
  across Budget, forecast and common modules; all 134 unfiltered mutants died.
- The Windows-name review fixture produced five expected failures. Fixed the
  exact device-name guard and added ordinary near-matches, generated-series
  invariants and an output-file collision contract. Ninety-eight focused tests
  retained 100% line/branch coverage; the subsequent collision contract passed
  in the eighteen-test shared-helper suite. Final mutation/full gates follow.
- Live BEFU extraction matched ten rows with 60 lineage rows and 2,332 cell
  dispositions (22 context, 10 normalized, 2,300 preserved-only, zero rejected).
  HYEFU matched ten rows with 60 lineage rows and 2,333 dispositions (22 context,
  10 normalized, 2,301 preserved-only, zero rejected). Two independent runs per
  source produced identical bytes; Bronze CAS verification and post-run hashes
  confirmed unchanged originals. Observation times record local source-object
  verification, not new HTTP retrievals.
- Final focused mutation run passed 99 tests and killed all 135 unfiltered
  mutants, with zero survivors/pardons. Report SHA-256:
  `1dfd39d29165a5e7cbe14bd24b8434f8c1e73a889965e575373cf9f2432ac1f1`.
  The complete health-domain run passed 161 tests, with 100% line/branch
  coverage across Budget, forecast, shared helpers and format inventory.
  Eight pre-existing SQLite ResourceWarnings remain visible.
- Rebuilt both live sources again using the final implementation into new
  external archive directories `silver/raw-befu-20260830-forecast-v1` and
  `silver/raw-hyefu-20260830-forecast-v1`. Every output, including each manifest,
  matches the earlier independent runs byte for byte; original hashes still
  match. No prior directory or published product was overwritten.

## 2026-08-30 — Original Budget extraction

- Resumed from clean main `7279629`. The baseline full harness exited zero
  with 1,247 passing tests and 95.60% coverage, including all supply-chain gates.
- Recompiled the three hash-pinned donor scripts without import/execution.
  Inspection and analysis compile; processing raises IndentationError at line
  199 after the duplicate `if` at line 198. Static behavior and failure modes
  are recorded separately from observed SQLite contents.
- The new raw Budget test initially failed collection because the adapter did
  not exist. First implementation exposed a tuple/list JSON receipt mismatch;
  canonical JSON-compatible receipt values fixed it. One follow-up command
  named a nonexistent test file and ran no tests; the corrected entire-domain
  command below is the valid coverage evidence.
- Commit `d26e769` adds the named-column original-workbook extractor, bounded
  verified snapshot, exact decimals, row dispositions, all-column source-cell
  lineage, new-directory-only outputs and a command-line entrypoint.
- Forty-nine focused tests passed at 100% line/branch coverage. All 73
  unfiltered generated mutants were killed; report SHA-256
  `6d85d73a824de888f7e232a5c41ef254f633d42ddd7f66b58661e8aea3e391c9`.
  The whole health-domain suite passed 111 tests with 100% coverage for both
  Budget extraction and format inventory. Eight SQLite ResourceWarnings were
  reported by that suite; no test failed. Ruff and basedpyright passed.
- Live extraction accounts for all 6,504 Budget input rows: 215 normalized,
  6,289 non-Health exclusions, zero blank/rejected rows and 3,655 lineage rows.
  All seven donor appropriation fields match in source order. The mixed-year,
  mixed-amount-type sum `163181604.000` is a parity checksum, not an analytical
  aggregate. Bronze CAS verification matches the original workbook digest.
- A verified copy of the four output files is retained separately at
  `silver/raw-budget-d26e769` under the existing external archive root. Manifest
  digest: `03f41d39395b02169202e88e98f04a892a3dbb55c2083a328391d909af8f7d57`.
  This is a local validation derivative using a fixed reproducibility-time
  context, not a new capture-time attestation or approved publication candidate.
- Read-only next-source inspection recorded Actual/Forecast ranges, literal
  versus cached-formula totals, fiscal-period/basis transitions and annotated
  years. It does not claim those adapters have been implemented.
- A second independent extraction produced byte-identical Parquet files and
  completion manifest. The original digest remained unchanged. Both rebuilds
  completed without evaluating formulas or accessing external links; observed
  runtime was slow under shared machine load, not an unreported failed run.
- The final full harness exited zero: 1,296 tests, 95.66% coverage, 30 schemas,
  20 representative documents, 9/9 parity checks, all repository mutation and
  supply-chain gates, and a validated 110-component SBOM. Eight SQLite warnings
  were recorded. The post-bookkeeping track-status test also passed. Unrelated
  timestamp-only evidence churn from the harness was inspected and restored.

## 2026-08-30 — Opaque workbook parts and external references

- Five new fixture cases produced four passes and one expected failure:
  `xl/notvbaProject.bin` incorrectly set the macro marker because detection
  matched a suffix rather than the exact part basename. External-link and
  opaque-part tests characterize existing behavior; they do not manufacture a
  failing implementation contract.
- The initial full run collected the new test before its fix, and overlapping
  coverage runs shared the default coverage store, invalidating both coverage
  reports. No baseline success is claimed. Validation is rerun sequentially
  against fixed files; subsequent coverage runs must not share an active store.
- Sequential focused validation passed 37 tests at 100% format-module line and
  branch coverage; all 31 unfiltered mutations were killed. Ruff and basedpyright
  passed. Functional commit: `ee54bc9`; continuation route: `3932caf`.
- Fresh `./scripts/validate.sh` exited zero: 1,247 tests, 95.60% coverage,
  30 schemas, 20 representative documents, 9/9 parity, all mutation lanes,
  dependency/licence/secret checks and a 110-component SBOM. Eight existing
  SQLite ResourceWarnings remain. Unrelated timestamp-only churn was restored.
- Offered a same-task hourly heartbeat via the app's suggested-create card
  after finding no matching existing automation. This is not active-run evidence
  or a new publication/retirement approval; activation is a user choice.

## 2026-08-30 — Current-state reconciliation

- Found the entry page reporting scaffold-era state despite canonical metadata
  recording publication and partial implementation. A focused status contract
  failed as expected because `new` disagreed with `in_progress`.
- Public HF API readback confirmed revision
  `9b85bac06597d4435fd078f6bed0f30bb008542b` and collection item
  `6a92b824597df1d081fc4108`. This was metadata readback, not another byte audit.
- GitHub reported parent #205 closed on 2026-08-29 despite unfinished plan
  tasks. Donor readback still reported unarchived. No source or hosted payload
  was changed by these checks.
- Corrected the entry page and verified the focused regression test, Ruff and
  basedpyright. Reopened #205 with a bounded explanation; independent readback
  returned `OPEN`. This is a traceability correction, not a new scope approval.
- Commit `11117f7` contains the correction and offline contract. Baseline
  `./scripts/validate.sh` exited zero with all schema, parity, mutation and
  supply-chain gates, including a 110-component SBOM. The updated full pytest
  suite passed 1,242 tests at 95.60% coverage (eight SQLite ResourceWarnings).
  The new test passed separately with Ruff, formatting and basedpyright checks.
  No production code changed, and timestamp-only unrelated receipts were restored.

## 2026-08-30 — Rich workbook census

- Continued from verified main `b85e02a`; selected the Phase 1.3 inventory
  detail slice under M-07/S-03, not publication or donor retirement.
- Red: `uv run pytest -q tests/domains/health_appropriations/test_workbook_census.py`
  failed with missing inventory `schema_version`. The synthetic fixture also
  requires explicit ranges, hidden spans, formula/comment coordinates, scoped
  names and package parts, while checking unchanged bytes and repeatability.
- Focused green: 28 tests passed with 100% format-module line/branch coverage.
  Ruff requested a smaller fixture helper. Strict typing identified nullable
  column-span endpoints and the inferred active-sheet chart API. Keyword
  adjustments did not resolve the chart diagnostic. Runtime source inspection
  confirmed anchor assignment is equivalent, so the fixture now sets
  `chart.anchor` and calls the shared single-argument `add_chart` API.
- The first mutation run killed 19/23 mutants. Its report selected only the
  scan-budget property test for all four survivors (formula comparison,
  expanded-size boundary and two load options). Added exact package-budget
  boundaries and a loader-options contract; rerun disables coverage filtering
  to exercise the full focused suite for each mutant.
- Unfiltered mutation rerun: 23/23 killed and 30 focused tests passed.
- Baseline harness reached SBOM after 1,236 passing tests and preceding gates,
  but uv launchers remained running with defunct Python children and an empty
  SBOM file. Stopped only this run's two launchers after SIGTERM did not work.
  The interrupted baseline exited 137 and is not a full-pass receipt.
- Bounded environment correction: invoked `tools/supply_chain.py sbom` through
  the repository `.venv/bin/python` with its bin directory on PATH; it passed
  with 110 validated components. Started a fresh full harness for final code.
- Final `./scripts/validate.sh` exited 0: 1,239 tests, 95.59% coverage,
  30 schemas/20 representative documents, 9/9 parity, all mutation lanes,
  format/lint/types, audit/licences/secrets and a validated 110-component SBOM.
  The format module retains 100% line and branch coverage in the full suite.
- Functional commit `dffa310`; restored only four unrelated timestamp-bearing
  harness receipts. Source payloads and existing published manifests are
  unchanged. Cached-value interpretation and broader track work remain open.

## 2026-08-30 — Workbook safety prerequisite

- Continued from merged status PR #223 (`75c0ca9`) on a clean checkout.
- Selected the still-open Phase 1.3 safety prerequisite before expanding
  CLI/scheduled operations; no donor or publication mutation is in scope.
- Red command: `uv run pytest -q tests/domains/health_appropriations/test_workbook_bounds.py`.
  Observed 8 failed and 3 passed: Windows-style/ambiguous paths and duplicate
  parts reached the parser rather than being rejected; the cumulative cell
  scan limit was absent. Existing POSIX traversal rejection was characterized.
- Green: 27 focused tests passed, including 20 generated sparse-extent/budget
  examples; `formats.py` has 100% line and branch coverage. Ruff's import and
  raw-regex findings were corrected without changing behavior.
- Mutation: `uv run pytest -q tests/domains/health_appropriations/test_inventory.py tests/domains/health_appropriations/test_workbook_bounds.py --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/formats.py --gremlin-report=json --gremlin-workers=4`
  killed 22/22 mutants; no survivors. The property test was added afterwards
  and included in the subsequent focused/full validation.
- `./scripts/validate.sh` passed: 1,236 tests, 95.59% overall coverage,
  30 schemas/20 examples, 9/9 parity, all targeted mutation lanes, formatting,
  lint, strict types, dependency audit, licences, secrets and 110-component SBOM.
  Existing SQLite ResourceWarnings were observed; no test failed.
- Restored only the four inspected unrelated timestamp-bearing receipts.
  Functional commit: `b2956a7`. Hosted checks/publication are not inferred from
  the local harness. The full track and broader Phase 1.3 task remain open.

## 2026-08-29 — Track initialization

- Confirmed the repository root at
  `/Volumes/PortableSSD/GitHub/archive-govt-nz` and preserved a clean worktree
  on local `main`, which was 17 commits ahead of `origin/main` before this
  scaffold.
- Read the project definition, requirements, design, technology stack,
  workflow, autonomy policy, tracks registry and applicable repository rules.
- Ran `./scripts/validate.sh` before scaffolding. The full local baseline
  passed: lock, formatting, lint, strict typing, 1,161 tests with 95.36%
  coverage, schemas, parity, mutation lanes, hygiene, CAS benchmark,
  dependency audit, licence checks, secret scan and SBOM validation.
- The validation harness updated four timestamp-bearing evidence receipts.
  Their diffs were inspected and restored as known generated churn; no
  substantive evidence change was retained.
- Cloned the public donor read-only and pinned commit
  `4668e6c3b1b492086941d4c1ef96e299250a8301`, tree
  `c6d44ff79eda73cfc6ba7db5764e27ce01b890e1`, and deterministic Git archive
  SHA-256
  `9c8ab0feaa752ead08163463a634623d55a62a69608772b73127b3d7b709157e`.
- Verified the donor inventory contains 23 tracked files (6,604,301 bytes):
  eight original source files, one five-table/312-row SQLite database, three
  Python scripts, six PNG plots, and five documentation/licence files.
- `python -m py_compile process_data.py` identified an `IndentationError` in
  the donor. This is characterization evidence and a regression target; donor
  code was not executed as trusted production code.
- Inspected the current Hugging Face HEOR collection read-only. It exists and
  was public; only `edithatogo/reimbursement-atlas` was observed as a member.
  No health-appropriations dataset was created or uploaded.
- The spreadsheet capability lookup reported that bundled workspace workbook
  dependencies were not configured. No alternate parser was silently used;
  executable workbook inventory and dependency evaluation are explicit Phase
  1 tasks.
- Reviewed official discovery leads for Treasury/Budget Vote Health and fiscal
  series, Ministry of Health Vote Health series, Pharmac CPB, and Stats NZ
  context. These remain planning observations pending a live cutoff-bound
  source census and resource-level rights evidence.
- User explicitly approved the revised medallion-aligned specification and
  plan, including complete original retention and the direct/indirect dataset
  recommendations.

## Initialization boundary

No source payload was copied into this repository, no archive CAS was mutated,
no new dependency was adopted, no external issue was created, and no GitHub or
Hugging Face publication state was changed during planning.

## 2026-08-29 — Post-scaffold validation

- Track structural checks passed: all 19 Must requirements and all 16
  acceptance criteria appear in the plan; all ten required artifacts exist;
  metadata and four JSONL evidence records parse; the registry link resolves;
  and `conductor/index.md` is unchanged.
- `./scripts/validate.sh` passed after the scaffold: lock, Ruff format/lint,
  basedpyright, 1,161 randomized tests in 190.84 seconds, 95.36% coverage, 30
  schemas and 20 representative documents, 9/9 parity checks, every targeted
  mutation lane, zero hygiene findings, 590.54 MB/s CAS benchmark, no known
  dependency vulnerabilities, licence inventory, source-scoped secret scan,
  and a validated 102-component CycloneDX SBOM.
- Four harness-generated timestamp-only evidence diffs were inspected and
  restored. They were unrelated to this planning track and are not included in
its change set.

## 2026-08-29 — Phase 0.1 implementation baseline

- Re-observed local commit `160d1705ee93d898c635f094fe98d8ae14d16695`
  and remote `main` at `b5f736010a47f5a260dca35d5ee3f4dbcadb4de7`.
- Re-cloned the donor read-only at its pinned commit. Its remote ref, tree,
  no-prefix deterministic Git archive digest, 23 paths, 6,604,301 bytes,
  eight originals, five SQLite tables/312 rows, three scripts and six plots
  all match the planning baseline. A prefixed archive has a different digest,
  as expected; the receipt therefore names the no-prefix archive contract.
- Observed all eight official landing-page leads. Pharmac and both Stats NZ
  pages returned HTTP 200; the four Treasury/Budget pages and Ministry page
  returned bounded HTTP 403 responses to the command-line client. These are
  availability observations, not source-item dispositions or capture claims.
- Confirmed Hugging Face authentication as `edithatogo`, absence of the target
  dataset, and one existing HEOR collection member. No matching GitHub issue
  exists. No hosted state was changed during this reconciliation.
- Recorded the local toolchain versions for `uv`, Python, GitHub CLI,
  Hugging Face CLI and Git. DuckDB and LibreOffice executables were not found
  on `PATH`; repository-managed Python capabilities are evaluated separately.

## 2026-08-29 — Phase 0.2 hosted issue hierarchy

- Created parent GitHub issue
  [#205](https://github.com/edithatogo/archive-govt-nz/issues/205) and phase
  issues #206 through #216 under the user's explicit instruction to complete
  the remaining track work.
- Added all eleven phase issues as GitHub sub-issues of #205 and independently
  read the hierarchy back through the API. Issue creation is now evidenced;
  issue closure remains tied to the corresponding phase evidence.

## 2026-08-29 — Phase 0 checkpoint

- Reviewed the reconciled baseline for drift, unsupported completion claims,
  credentials, signed URLs and restricted payloads; no actionable finding was
  identified.
- `./scripts/validate.sh` passed: lock, format, lint, strict typing, 1,182
  tests in 121.17 seconds, 95.33% coverage, 30 schemas, 20 representative
  documents, 9/9 parity checks, all mutation lanes, hygiene, 423.38 MB/s CAS,
  dependency audit, licence inventory, secret scan and a 102-component SBOM.
- Four known timestamp-bearing validation receipts were inspected and restored
  rather than retained as unrelated generated churn. This is local Phase 0
  readiness evidence, not hosted CI or publication evidence.

## 2026-08-29 — Donor Bronze import and first source census

- Added typed, fail-closed source inventory and donor-manifest contracts plus
  safe XLSX/PDF/SQLite structural inventory.
- Imported all 23 donor paths (6,604,301 bytes) into 23 immutable SHA-256/BLAKE3
  objects outside Git and verified every object from the generated manifest.
  The manifest and format-census SHA-256 digests are recorded in machine
  evidence; payload paths are intentionally not committed.
- The seven workbooks contain 152 sheets, 2,388 formula cells, two hidden
  sheets, 5,777 named ranges, six charts and 11 external links. The PDF has
  471 pages; the five-table SQLite derivative has 312 rows. Inventory did not
  mutate an original.
- Built a 2026-08-29 census with 79 official records: 66 links exposed by the
  complete Vote Health index and 13 current direct/context resources. All are
  `discovered`; none is mislabeled captured or rights-cleared. Earlier annual
  Budget/forecast vintages and exact Stats NZ QES/population series remain to
  enumerate before Phase 1 completeness.
- Adopted locked `openpyxl` and Matplotlib adapters without adding Pandas.
  Focused tests and strict typing passed. Dependency audit and licence
  inventory passed; a scanner keyword false positive in existing machine
  evidence was renamed without suppression, after which the tracked-source
  scan and 110-component SBOM passed.
- The first staged-source scan failed closed on one unverified keyword finding:
  a machine-evidence key named `secret_scan`. Inspection of the bounded receipt
  confirmed that no token or credential was present. The field was renamed to
  `tracked_source_scan`; no detector suppression was added, and the staged
  source scan then passed with zero candidates.

## 2026-08-29 — Bronze through Platinum implementation checkpoint

- Expanded all 66 historical Vote Health edition pages to 58 unique official
  PDFs, including the two directly resolved 2012/13 supplementary-estimates
  files. Added current Budget/BEFU/HYEFU/Fiscal Time Series, Ministry Vote
  Health, Pharmac CPB, and exact Stats NZ CPI, QES, population-benchmark and
  current-price GDP inputs.
- Closed the cutoff-bound census at 141 records: 73 captured originals and 68
  discovery-only pages represented by their authoritative resources. No item
  remains discovered or retryable. The complete capture contains 73 matching
  WARC receipts and 38,584,141 source bytes in immutable external CAS.
- Produced 312 typed Silver facts and 1,699 field-lineage records from the
  verified donor parity oracle. Rebuilt its five-table SQLite database with
  exact row/value parity, five analytical Parquet products and all six plots.
- A clean-room rebuild from Bronze reproduced both Silver Parquet digests and
  all 12 Gold artifact digests byte-for-byte when supplied the pinned
  observation time. A deliberately different observation time changed the
  bitemporal facts digest, demonstrating that time is part of the identity.
- Built candidate v4 with 94 pre-manifest files and 39,390,246 bytes. Its
  manifest SHA-256 is
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`;
  rights and source-disposition gates pass, while upload remains gated on
  explicit approval of this exact manifest.
- Final local `./scripts/validate.sh` passed at commit
  `f32f0fbdb223fa0358c91defcc749ce9cb739d2f`: 1,200 tests, 95.16% coverage,
  30 schemas, 20 representative documents, 9/9 parity checks, all mutation
  lanes, hygiene, CAS benchmark, dependency audit, licences, secret scan and
  110-component SBOM. Seven resource warnings were reported but did not fail
  the harness; they are not hidden.

## 2026-08-29 — GitHub merge and Hugging Face publication

- PR #217 passed the exact-head Ubuntu, macOS and Windows assurance matrix,
  CodeQL, dependency review, workflow-policy lint and Codecov patch gate, then
  squash-merged to `main` as `622ec15d53b162916a0b1b390ec5dab6f2f6f3a7`.
- Reverified candidate manifest SHA-256
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`
  and all 94 recorded file hashes before upload.
- Published `edithatogo/nz-health-appropriations` at revision
  `9b85bac06597d4435fd078f6bed0f30bb008542b`. Fresh remote download verified
  the same manifest and all 94 entries with zero mismatch.
- Added the dataset to the HEOR collection. Independent collection readback
  returned item object ID `6a92b824597df1d081fc4108` with the manifest and
  revision recorded in its note.
- Post-publication `./scripts/validate.sh` passed with 1,215 tests, 95.55%
  coverage, 30 schemas, 20 representative documents, 9/9 parity checks, all
  mutation lanes, hygiene, supply-chain audit, licence and secret checks, and
  a validated 110-component SBOM.

## 2026-08-30 — Review fix: property-test timing stability

- A current full harness run reached 1,214 passing tests but Hypothesis marked
  `test_selected_resources_are_always_policy_eligible` flaky after one
  generated example took 285.81 ms under parallel startup load and exceeded
  the default 200 ms deadline; the identical example then completed in 0.02 ms.
- The focused test immediately passed on rerun. Disabled the wall-clock
  deadline only for this pure invariant test while retaining all generated
  examples and assertions. The four-test module passed under the repository's
  xdist configuration; Ruff and basedpyright passed.

## 2026-08-30 — Read-only health operational status

- Added red contracts for no-state, partial, ready and corrupt-manifest
  behavior. Collection initially failed because the operational module and
  CLI entrypoint did not exist.
- Implemented a shared fail-closed manifest reader exposed as
  `health-appropriations-status` in the CLI and as the read-only MCP tool
  `health_appropriations_status`. It reports bounded counts, layer presence,
  dataset identity and candidate-manifest digest and performs no capture,
  transformation, publication or retirement action.
- A live smoke test initially exposed an ambiguous donor glob selecting the
  format census. Manifest selection was narrowed to commit-shaped filenames;
  the live archive then reported `ready`, 23 donor files, 73 captured official
  resources, 312 Silver records and the published candidate digest.
- Thirty-six focused CLI/MCP/domain tests, Ruff and basedpyright passed. The
  critical operational module reached 100% line and branch coverage.

## 2026-08-30 — Formula cache observations

- Two new red contracts failed on missing cache inventory and freshness fields.
  The fixture distinguishes numeric zero, boolean false, string, stored error,
  and absent/empty cached results without permitting formula evaluation.
- Implemented presence/type-only observations in `f73d678`, using the existing
  parser's data-only view for formula coordinates. Repeated inventory is
  deterministic and fixture source bytes remain identical.
- Thirty-two focused tests passed at 100% format-module line/branch coverage;
  all 30 unfiltered mutations were killed. Ruff and basedpyright passed.
- Baseline and final `./scripts/validate.sh` runs exited zero. Final validation
  passed 1,241 tests at 95.60% coverage, 30 schemas, 20 representative documents,
  9/9 parity checks, all repository mutation lanes and supply-chain gates,
  including a validated 110-component SBOM. Eight SQLite ResourceWarnings
  were emitted by the full test run; no test failed.
- Timestamp-only unrelated evidence churn was restored. No originals or
  published artifacts were modified. Live GitHub readback still reports the
  donor repository as unarchived; retirement remains outside this track.

## 2026-08-31 — Standalone Budget receipt operations

- Added matching pinned read-only CLI/MCP receipts and a strict shared schema.
  Failures retain structured receipts while redacting source/parser diagnostics.
- Fifty-two focused tests passed at 100% helper line/branch coverage; formatting,
  lint, typing, 41 schemas/31 samples and 70-track Conductor validation passed.
- Required native gate emitted 2,030 passed/two timing failures at 96.81% overall
  coverage, then exited 124. Both unchanged failed tests passed in isolation.
  This is not a complete local gate pass; hosted assurance remains separate.
- Live retained Budget-2026 package verified 185 facts, 3,145 lineage rows and
  all 6,451 dispositions. No original or published byte was changed.
- Checkpoint/recovery into an independent clone preserved work during external
  worktree removals. The precise receipt and browser blocker are documented in
  [Budget operations](./budget-operations.md).

## 2026-08-31 — Hash-bound embedded-notice observer

- Red import contract established; 34 focused tests reached 100% line/branch
  coverage, followed by 29/29 cold unfiltered mutant kills. Independent review
  found no implementation defect. Ruff, typing, secrets and Conductor pass.
- All three exact reviewed Bronze workbooks returned notice observations,
  without source text or eligibility promotion. Originals remain unchanged.
- Required native gate emitted 2,215 passed and one existing CPI timing failure
  at 96.91% coverage, then exited 124. The unchanged failed test passed alone.
  No deadlines were weakened; hosted assurance remains separate. Exact bounded
  receipts are in [embedded notices](./embedded-notices.md).

## 2026-08-31 — Exclusive local additive staging

- Began an independent branch after the pinned inventory planner; PR #290 was
  subsequently observed merged after all seven hosted checks succeeded.
- Established a missing-module red contract, then 27 focused passing staging
  contracts. No original, candidate, or Hugging Face payload was changed.
- The new local-only layout preserves the historical manifest/card separately,
  emits no active candidate manifest, and records completion only after full
  copy readback. Review and heavier validation remain pending; see
  [additive staging](./additive-staging.md) for the bounded contract.

- Independent review found non-finite JSON acceptance in inherited inventory
  metadata; seven red cases drove strict finite parsing/encoding. The combined
  139-test suite now has 100% critical line/branch coverage and 120/120 cold,
  unfiltered mutant kills with zero survivors/timeouts/errors/pardons/cache hits.
- Final-source local replay preserved all 113 listed files and matched both the
  earlier pilot and a second fresh build. No candidate or publication changed.
- Native validation completed with exit zero: 2,631 tests, 97.02% coverage,
  all repository gates and a validated 111-component SBOM. Eight existing
  SQLite ResourceWarnings remain disclosed. Hosted delivery is a separate gate.

## 2026-08-31 — Additive record-set structural contract red phase

Self-review rejected the first Decimal256 carrier: a synthetic DuckDB Arrow
registration probe failed with `NotImplementedException` (unsupported Decimal
76/38/256). Nothing was persisted. Use the established Decimal128(38,18) for
this bounded structural version, with explicit representability limits and a
negative overflow fixture; do not claim it represents every possible value
in every source schema. Wider values remain in original/source-specific
packages until an explicitly compatible projection exists. Test DuckDB
queryability as part of the contract rather than assuming Parquet suffices.

`uv run pytest tests/schemas/test_health_recordsets.py -q` first failed collection
with the expected missing `health_recordsets` module (exit 2). The initial
implementation then passed nine tests and failed all eight exact Parquet
schema round trips (exit 1). A bounded independent field comparison identified
Arrow's default list child name `item` versus Parquet's `element`, not numeric
or source-data loss. Correct the new schema's list child names explicitly;
do not weaken exact schema equality or rewrite any existing package.
Focused Ruff also identified missing test docstrings and tuple parameter syntax.
No source payload, archive package or hosted publication was modified.
## 2026-08-31 — Record-set native assurance

At head `6895083`, the required
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
completed with exit 0. Results: 71 Conductor tracks; format/lint/strict typing;
2,424 tests and eight warnings in 86.38 seconds; 96.98% overall coverage;
41 schemas/31 representative documents; 9/9 parity; all repository mutation
lanes; hygiene, vulnerability audit, licences, secrets and 111-component SBOM.
CAS benchmark: 521.48 MB/s. Durable native log SHA-256:
`fdea8f19263999b33dea5583e6635dc5477ff730c4697f8f55d1c665d61f6507`.
Only the four task-generated timestamp-only receipt diffs were restored after
the process stopped. Earlier red-phase evidence remains intact.

Focused mutation command:
`uv run pytest tests/schemas/test_health_recordsets.py -q --gremlins --gremlin-targets=src/archive_govt_nz/schemas/health_recordsets.py --gremlin-report=json --gremlin-parallel --gremlin-workers=1 --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov`.
All 34 tests and 30 mutants passed with no filtered tests or cached results.
## 2026-08-31 — Record-set integration path correction

Corrected post-integration command passed 52 tests in 3.49 seconds, and the
Conductor validator passed all 73 tracks. Native assurance remains tied to
the earlier exact head; production and test hashes did not change on merge.

After integrating main `6885c3e` (merge `aed6c31`), the focused command named
nonexistent `tests/test_conductor_state.py`: exit 4, no tests ran. File discovery
identified `tests/tools/test_validate_conductor_state.py`; rerun the corrected
path with the 34 schema tests. Production/test hashes remain unchanged and the
entire incoming machine ledger was verified byte-for-byte as a prefix before
appending the two owned schema receipts. This does not replace the separately
recorded pre-integration full harness.
## 2026-08-31 — JSON row-shape red and focused phase

The new JSON-schema test initially failed collection with the expected missing
`health_recordset_json` module (exit 2). Initial implementation passed 37 tests;
Ruff identified a long description line and test parameter container style,
corrected without changing policy. Expanded exact-decimal property and integer
boundary checks then passed 40 tests with 100% critical coverage (17 statements,
two branches). An additional unsupported-binary-type regression proves there
is no generic text fallback. Native/mutation gates remain pending for this
increment; earlier Arrow-only native assurance is not reused as full coverage.
No original, existing schema, stored derivative or publication was changed.

### JSON final focused assurance

The final 51 tests passed with 100% line/branch coverage (17 statements, two
branches). Ten seeded descriptor counterexamples separately check weakened
generated contracts; they are not additional source-code mutations. Two
independent read-only reviews found no actionable structural-scope defect.
The final cold, unfiltered one-worker mutation command used all 51 tests:
`uv run pytest tests/schemas/test_health_recordset_json.py -q --gremlins --gremlin-targets=src/archive_govt_nz/schemas/health_recordset_json.py --gremlin-report=json --gremlin-parallel --gremlin-workers=1 --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov`.
It passed in 14.02 seconds, killing both generated mutants with zero survivors,
cache hits, timeouts, errors or pardons. A coverage module-not-measured warning
in this no-coverage mutation invocation is not the separate coverage result.
Report SHA-256: `ff6d4618b8e5b523bbf405a0e442c0ced6e4ab37f0a638595e9ef53c0e23dd78`.
Native assurance remains pending; publication and originals remain untouched.

## 2026-08-31 — JSON integrated native assurance and delivered-state reconciliation

At integrated head `d71d431`, the required
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
completed with exit 0: 2,796 tests, eight warnings, 61.41 seconds, 97.05%
coverage; 73 tracks; format/lint/strict types; 41 schemas/31 documents; 9/9
parity; all repository mutation lanes; hygiene, audit, licences, secrets and
111-component independently validated SBOM. CAS measured 526.31 MB/s.
Native log SHA-256:
`f7f73fe959b3a14f3642a20e557db43bc31cd437c839e603176db7f252ce17e2`.
Two owned timestamp-only fixture diffs were restored after process completion.
No original or stored derivative changed. JSON hosted delivery remains pending.

Integration preserved incoming main `ad28694` and its complete evidence ledger,
then appended the owned JSON receipt; conflicts were documentary only. Parent
Arrow PR #293 was observed merged at head `5ffb651`, merge `ad28694`.
Fresh REST readback also confirms Budget operations PR #280 (head `199c82b`,
merge `113bac5`) and read-only inventory PR #290 (head `a8f54f5`, merge
`07143c8`). Their two stale in-progress bounded tasks are reconciled without
claiming broader operational or publication readiness. Prior local failures
remain in the ledger. The attempted optional guide path
`conductor/platform-guides.json` was absent; file discovery found no root
platform-guide manifest. General/Python guides and repository workflow apply.

## 2026-08-31 — Historical snapshot reader red and transport mismatch

Initial focused collection failed with the expected missing snapshot module
(exit 2). The first implementation passed 11 negative tests but rejected its
valid writer-generated fixture. A bounded private-helper traceback isolated
exact schema comparison; independent field comparison found only historical
`quality_flags` and `footnotes` child names: in-memory Arrow `item`, stored
Parquet `element`. Freeze explicit transport names for those fields, preserving
metadata/type/nullability checks and all existing files. This is a reader
contract correction, not source rewriting or ignored schema drift. Ruff also
identified exception-literal/import/raw-regex styles; strict typing passed.

### Historical snapshot focused and live assurance

After the explicit transport child-name correction, 49 tests passed in 2.22s,
100% critical coverage (76 statements, ten branches). Ruff and strict typing
passed. Independent read-only review found no actionable issue; exact-cap
boundaries and complete-hashes-before-decode tests were added. The deep JSON
fixture is bounded by manifest admission and tested as a redacted failure;
no separate recursion-handling claim is made.

Cold unfiltered mutation used all 49 tests, one worker, a clear cache and zero
pardons: 57/57 killed, no survivors/timeouts/errors/cache hits, 66.08s.
Command: `uv run pytest tests/domains/health_appropriations/test_historical_snapshot.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/historical_snapshot.py --gremlin-report=json --gremlin-parallel --gremlin-workers=1 --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov`.
Report SHA-256 `c75a74651ce29feaf07e02ed718d2a2eaaaf456fe01de1ba193451e4b88b62c8`.
Source/test SHA-256 respectively
`781e436fb2a3e414b1de78c2ab8bd1be30e478c080f3e697070c18497bf4c261`
and `e0a470091c2cfa8c8c3e78ead2a6cef511a5c87342d43b8279431cf399bae925`.

Local reads verified both historical manifests, all six Parquet files and
both original objects, totaling 449,487 and 337,077 bytes respectively.
No source/package/candidate write or workbook execution occurred. Functional
commit `7a0420e`; main `6c23ba8` integrated without conflict before the native
run. Entire incoming machine ledger is retained; snapshot evidence is appended.

## Native assurance — 2026-08-31

The required `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
passed at `b649de6` with exit 0: 2,918 tests, eight warnings, 68.44 seconds,
97.10% coverage; 74 Conductor tracks, format/lint/strict typing, 41 schemas/31
samples, 9/9 parity, all repository mutation/security/supply-chain gates and
111-component validated SBOM. CAS throughput was 512.18 MB/s. Log SHA-256:
`703d69135ac8fb84a2759303f36306fc1e26b738bf6b6636ac01d018789c4328`.
Two owned timestamp-only fixture diffs were restored after the process ended.
Hosted assurance remains pending; originals, derivatives and publication are
unchanged. This successful harness does not add a semantic or rights claim.
## 2026-08-31 — Pure historical canonical projection

In independent clone `health-historical-canonical.8ijp7V`, implemented pure
`project_historical` on merged structural registry base `ad28694`. No original,
reader, publisher, candidate or HF operation changed. Initial import and targeted
dependency, Decimal rendering, Parquet-list and observed context-label tests
failed before their fixes. Nine independent-review regressions likewise failed
before source-cell join and unused-field corrections. The final focused run
passed 121 tests in 0.65 seconds, targeted typing and Ruff passed, and critical
coverage passed 184 statements/32 branches at 100% in 0.71 seconds. The two
year-boundary positive fixtures needed their disposition literals synchronized;
that intermediate two-failure result is retained here, not attributed to code.

Read-only pilots checked two manifest pins plus six Parquet hashes, projected
each twice identically, verified disjoint cross-vintage IDs and unchanged source
package file hashes. Counts are 53/53 and 54/54 canonical facts, 1007/1026
canonical lineage, with all 1143/1164 original lineage rows accounted. No
canonical files were persisted and original workbook fixity is not claimed by
this pilot. Full details and source/test hashes: `historical-projection.md`.

Cold mutation command (one worker, no coverage filter, cleared cache, unchanged
default 30-second deadline and zero pardons):
`COVERAGE_CORE=ctrace PYTHON_JIT=0 .venv/bin/pytest tests/domains/health_appropriations/test_historical_projection.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/historical_projection.py --gremlin-report=json --gremlin-workers=1 --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov`.
Cold mutation passed all 129 mutants in 164.86 seconds, with zero survivors,
timeouts, errors, pardons and cache hits. All 121 tests were selected without
coverage filtering despite the coverage-collection warning. Receipt SHA-256
`3a59033572caaec87024fb8e7df046b3d9d5e3936007920c80e88204fab122ff`.
The native `./scripts/validate.sh` is now running with `COVERAGE_CORE=ctrace`,
`PYTHON_JIT=0`, four xdist workers and an independent uv cache/interpreter.

Native completed exit 0 on Python 3.14.6/uv 0.11.8: 2,866 tests in 76.99
seconds, eight existing warnings, 97.08% coverage; 41 schemas/31 documents,
9/9 parity, all repository mutation and hygiene checks, CAS 474.63 MB/s,
audit/licences/secrets and SBOM 111 components passed. Native log SHA-256
`6f0e6f155498ce0bab244eee300222d6d8d985c5c0f93d80ba344d26e9090c7e`.
After the process exited, restored only the two test-generated timestamp-only
legislation receipt changes. Original source files and published data unchanged.

Functional checkpoint `596a73f` merged main `3be3048` as `47130c2`. Conflicts
were confined to append-only review/runlog/evidence records; incoming records
precede the owned records, and an explicit byte-prefix assertion passed for the
entire machine ledger. Source/test hashes remained unchanged. Post-integration
224 projection/schema/Conductor tests passed in 4.79 seconds, 1,641 files passed
format, repository Ruff/types passed, and all 74 Conductor tracks validated.
This is focused post-integration assurance, not another full native run.

PR #305 needed a second main integration after snapshot-reader PR #303 merged
as `2061098`. Merge `6da2b84` preserves all incoming ledger bytes as a prefix
and both projection events; 188 projection/snapshot/Conductor tests passed in
9.41 seconds, all 74 tracks and scoped lint passed. The append-merge helper's
temporary two-character header truncation was corrected before committing and
full JSON validity checked. Production/test hashes and native evidence are
unchanged; no second full run is claimed.


## Budget classification occurrence projection

The pure source-label projection passed independent read-only review, 42 focused
tests with 100% critical line/branch coverage and 29/29 cold mutant kills.
Two verified retained Budget packages yield 400 unmapped occurrence dimensions
and full 6800-row lineage accounting without input mutation. Exact Parquet
round-trip and source-object identity boundary tests pass. No authoritative
identifier, valid-time interval, crosswalk or rights promotion is invented.

Required native validation at `b651907` passed all 3014 tests (8 existing resource
warnings), 97.12% coverage and all subsequent gates. Two owned timestamp-only
fixture changes were restored after exit. Source and tests remain unchanged;
hosted delivery is pending. See [full receipt](./budget-classification.md).
## Forecast preflight local assurance — 2026-08-31T16:17:15Z

Checkpoint `a85ca41`: 92 focused tests, 100% critical coverage (131 statements,
52 branches), independent review and cold unfiltered 66/66 mutation kills pass.
Four final-code synthetic packages match all 16 pre-change output files exactly;
originals are unchanged. Initial unsupported-keyword, tuple/list and missing-scope
red failures were resolved; no test/gate was weakened. Full native/hosted delivery
remain pending. See [forecast-preflight.md](forecast-preflight.md).
