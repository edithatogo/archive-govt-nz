# Bounded source-profile operations

## Contract and scope

This M15/M18, AC13/AC16 slice exposes the existing CPI `CPIQ.SE9A`, Ministry
HAIR2024 Figure27/Figure28 and QES June2026 Table8 profiles. It does not add
source acquisition, change their stored schemas, infer a chosen denominator or
deflator, or promote source observations into health spending facts.

`health-appropriations-extract-source` defaults to dry-run. Only explicit
`--no-dry-run` enables the existing adapters' exclusive new-directory writes.
The MCP `health_appropriations_preflight_source` has no write flag and always
uses dry-run. Existing donor rebuild and archive-status readiness semantics are
unchanged. Forecast/historical profiles lacking dry-run remain outside this
dispatcher. Broader operational and annual source coverage remain pending.

Caller context is validated, not acquisition-attested. The wrapper rejects
query/fragment/user-info locators and returns only allowlisted profiles,
transformation, source hash, counts and optional derivative hashes. Paths,
locators, supplied vintage/time, source rows and parser diagnostics are not
included in receipts. Rights remain `not_evaluated`; publication remains
`local_validation_only`. Adapter execution is not standalone package closure
verification. Failed partial outputs are retained without claiming completion;
interrupts propagate. Existing paths and direct source/output symlinks reject.

## Evidence in progress

Synthetic red-first tests exposed two wrapper issues before correction: a
protocol schema error echoed an oversized signed locator, and a failed adapter
status could otherwise be relabelled successful. Fixed redaction is limited to
this MCP tool; an explicit expected adapter status is now required. No original
source bytes or external services were used by these tests.

Focused suite: 134 passed in 8.66 seconds, including all four profile dispatches,
CLI default/explicit-write argv, MCP closed input, false-y nonboolean controls,
source immutability, malformed context, partial evidence preservation and a pure
receipt-schema property. Ruff passed. An attempted `ty` invocation was unavailable
in the locked environment; no dependency was installed to bypass the native
typing lane. Native basedpyright subsequently passed with zero errors/warnings.

Critical assurance now passes 138 tests at 100% line/branch coverage (64
statements, ten branches). Cold unfiltered mutation caught all 31 generated
dispatcher mutants, no survivors/errors/timeouts/pardons/cache hits, one worker,
unchanged 30-second deadline, 153.92 seconds. Report SHA256:
`e7c42c9708d6736fe722476ae93f7e48b63cf36f2e5758ae9597a0c9ed280deb`.
This receipt predates adding the input schema's explicit draft declaration;
dispatcher functions are unchanged. The full CLI/MCP regression found that
missing declaration (303 pass, one failure); after correction, 304 passed in
12.80 seconds. Four additional executable seeded counterexamples separately
exercise CLI default dry-run, explicit write propagation, failed exit code and
MCP error redaction; baseline oracles pass and all four seeded defects fail.
These are scoped wiring checks, not whole legacy CLI/MCP mutation coverage.
First native launch stopped at lint because formatting moved two test-only
private-access annotations; corrected on the exact access lines. Second native
run at `08bf5b1` passed all 3,061 tests (eight existing resource warnings,
69.91 seconds, 97.11% coverage), schemas/parity/mutations and dependency audit,
then exited 1 at secret scanning: the synthetic user-info rejection fixture
looked like embedded credentials. The same fake URL is now constructed from
separate tokens; no secret-scanner allowlist or gate was changed. Second log
SHA256 `03855f24882acadaa9f7844ecd4525eb11e2e6f41143c07a370d2d559c082784`.
Post-correction focused tests: 143 passed; native schema registry now includes
the receipt fixture (42 schemas/32 samples), and secret scanning passes. Exact
2048/2049-character schema boundaries are covered.

Full native retry at `b425ca0` exits zero: 3,066 tests, eight existing resource
warnings, 102.39 seconds, 97.11% overall coverage; dispatcher 100%, MCP 100%.
All 42 schemas/32 samples, 74 Conductor tracks, 9/9 parity, native mutations,
dependency audit, licence/secret checks and strict 111-component SBOM validation
pass. CPython3.14.6, four pytest workers, ctrace and disabled JIT; no thresholds
changed. CAS benchmark 418.32 MB/s. Log SHA256
`21da6c82c5702e449bec3549a5fbe2f635b64eaa0539698020939d49d07afcb1`.
All dispatcher function/class ASTs are identical to the cold-mutation commit.
Latest main `2061098` is integrated after this run, preserving its complete
incoming evidence prefix plus these delivery receipts; no dispatcher/CLI/MCP
production code changes during integration. Hosted exact-head assurance pending.
Post-integration source/Budget/CLI/MCP regression: 309 passed in 13.83 seconds;
74-track Conductor validation and exact incoming JSONL-prefix check pass.
No gates or deadlines were weakened.

Independent read-only review found no actionable production issue within this
bounded dispatch. JSON Schema integer counts intentionally follow JSON numeric
semantics; trusted adapter functions emit Python integer counts.

## Preceding delivery receipts

QES PR298 was merged with expected-head checking after all seven checks passed
at `ca9bfeefdbd3099af9dba7fd9566f86a815e830e`. REST readback confirmed merge
`6c23ba8eac687e32ea8b509243dcc85037838238` at 2026-08-31T14:50:33Z.
Its originals and retained v1/v2 pilot packages were not changed by delivery.

JSON contracts PR300 was merged after fresh clean state and seven successful
checks at `34c51ac78892ff4d2876d00c6d891194b2291fe0`. Expected-head REST squash
merge/readback confirmed `3be3048658eb9b6f939d71739e2b3bad2f768f62` at
2026-08-31T15:01:37Z. Neither delivery deleted branches or worktrees. These are
code delivery receipts, not new source publication or semantic completeness.
