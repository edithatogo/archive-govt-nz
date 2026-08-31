# Exclusive local additive staging

## Scope

This library-only step prepares a new local copy; it does not build a publication
candidate, upload to Hugging Face, grant rights, inherit approval, or canonicalize
the versioned Silver packages. The four-profile inventory planner was delivered
in PR #290 (head `a8f54f5e60b8c73d50cbe2bd84231282cd8ccc45`, observed merged as
`07143c82979b9b5708c150990a9277cc6635f348` after seven successful hosted checks).

`StagingInputs` takes explicit pins for the base candidate manifest, capture
manifest, rights record, four package manifests and the serialized inventory.
Preflight reruns full inventory verification and requires exact canonical
inventory bytes. The inventory is not an independent source of authority.

## Layout and preservation

- `base-history/<base-manifest-sha256>/` preserves every listed base file and the
  original root `MANIFEST.json`, including the historical dataset card.
- `additions/` contains all sixteen inventoried package files under their
  versioned logical paths, without replacing or reinterpreting base files.
- `INVENTORY.json` preserves the exact pinned inventory bytes.
- A fresh root `README.md` explicitly limits claims to local staging.
- `LOCAL_STAGING.json` uses `archive-govt-nz.health-additive-staging/v1`, not the
  publication-candidate schema. It records completion only after exact file-set,
  byte-count and SHA-256 readback of all preceding files.

No active root `MANIFEST.json` is emitted. The original candidate manifest and
card are historical provenance, not current approval or claims about additions.
Semantic validation is `not_performed`; new derivative rights are
`not_evaluated`; publication approval is `not_granted`.

## Filesystem boundary

Callers must supply a nonempty list of candidate/publisher-configured roots to
exclude. Output must be a new directory with an existing parent, outside those
roots and all input roots. This does not discover global publisher configuration
or protect against arbitrary manual upload: generic publishing utilities can
accept arbitrary directories. A live pilot must at least exclude the official
archive `candidates` root and use a fresh temporary location.

Inputs are reviewed roots, not an adversarial filesystem sandbox. Source files
are rehashed on copy; directory reservation and file creation are exclusive.
Partial output is never removed or overwritten. On failure, a partial completion
marker is moved to `INCOMPLETE_LOCAL_STAGING.json` where possible; a bounded
`FAILURE.json` attempts to retain the exception class without private diagnostics.
Receipt/quarantine filesystem errors do not mask the original failure. Do not
treat incomplete or unexpected-file directories as completed staging bundles.

## Validation checkpoint

The missing-module test failed before implementation (exit 2, 3.05 seconds).
Initial four contracts passed, then 27 expanded focused tests passed in 5.69
seconds. These cover deterministic preservation, repinned inventory mismatch,
changed input pins, path overlap and symlinks, full readback, post-preflight input
changes, exclusive-copy collisions, partial completion and failed receipts.
Focused Ruff passed. At that checkpoint, critical coverage, cold mutation,
native validation and independent review were still pending.

### Independent review correction

Review found that the inherited planner accepted Python's non-standard JSON
constants in extra recorded-rights metadata. Seven red cases demonstrated
acceptance of `NaN`, `Infinity`, `-Infinity` and numeric overflow `1e999`, plus
non-finite staging serialization (seven failures, 4.53 seconds). Planner parsing
now rejects non-finite floats/constants and the staging encoder sets
`allow_nan=False`. Finite extra metadata remains retained, without interpreting
its rights semantics. An initial positive-test key typo was corrected after
138 passing tests and one test-only KeyError; no source behavior was weakened.

The refreshed combined suite passes all 139 tests at 100% line/branch coverage:
88 staging statements/18 branches and 125 planner statements/20 branches, 11.58
seconds. Ruff and targeted typing pass. Two independent read-only reviews found
no further substantive issue within the reviewed-root copy-integrity scope.
Subsequent mutation and native checkpoints are recorded below.
The earlier planner's 78-kill report remains historical evidence for its earlier
source hash and is not relabelled as validation of this JSON correction.

### Retained local pilot

Two new builds under `/tmp/health-additive-stage-pilot.mdPaiP/{first,second}`
produced identical bytes for all 113 listed files (41,379,895 bytes) and the
completion marker. The listing consists of 95 base-history files, sixteen
additions, the pinned inventory and the new notice. The marker hashes to
`c92284a920b0c0380f9728e64932d88e518359cf7af46daee62685a824e8469c`.
The official archive `candidates` root was explicitly forbidden; retained
archive files and all Hugging Face bytes were untouched. This first pilot
preceded the JSON strictness correction. The final-source replay into fresh
`/tmp/health-additive-stage-final-pilot.bH8GKM/{first,second}` produced exactly
the same files, byte counts and completion-marker hash. All earlier outputs
remain retained. Final pilot receipt SHA-256:
`ef71ac65bb44f591e2bbcdf129d9d626e5ed07590434f574cbb7ac34918357e3`.

### Mutation checkpoint

The combined cold unfiltered run killed all 120 mutants (41 staging, 79 planner)
with two workers and all 139 tests selected. There were zero survivors, timeouts,
errors, pardons or cache hits; the unchanged per-mutant deadline was 30 seconds.
The run completed in 141.50 seconds. Its JSON and stranded coverage bytes were
retained outside the checkout before subsequent validation. Native validation
is the next required gate, not implied by this targeted result.

The mutation report SHA-256 is
`c311016ac8284dfaab01af9a604a3428b2c705fa2da8127daeadfd5323ec06e7`;
the critical coverage report SHA-256 is
`0aeb38a4a26e02baf61cb9d7ba6357a0de8f76f8e38c51b8833019791bde39ac`.
After integrating main `6885c3e`, all four tested source/test hashes remained
identical. The only source merge conflicts were the planner additions from its
squashed PR; the strict JSON correction and new regression tests were preserved.

### Complete native validation

The required `./scripts/validate.sh` completed with exit zero using
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4` and a dedicated
uv cache. CPython was 3.14.6. All 2,631 tests passed in 110.93 seconds with 97.02%
overall coverage and eight existing SQLite ResourceWarnings. Lock, formatting,
lint, typing, 73-track Conductor, 41 schemas/31 samples, 9/9 parity, all native
mutation lanes, hygiene, benchmark, vulnerability audit, licence inventory,
secret scan and the validated 111-component SBOM passed.

Native log SHA-256:
`258eafbad7470bf4a9c1a76a4de0674caffc04f5248523685f56a1f0f5359bbb`.
Four unrelated timestamp-only generated evidence edits were restored after
checking their diffs. No source/package bytes or earlier receipts were removed.
This complete local gate does not assert hosted checks, merge or publication.

After PR creation, incoming MoH main `25f9fb5` caused a ledger-only conflict.
Integration preserves that incoming ledger as an exact prefix, followed by the
staging receipt. The tested staging/planner source and test bytes are unchanged;
post-integration focused/static checks are separate from the earlier full gate.

The subsequent integration with reviewed structural-recordset revision `5ffb651`
preserves its full ledger prefix and all staging observations. Both review and
run-log histories are retained. Staging, planner and recordset production/test
bytes are unchanged from their reviewed revisions. Combined focused validation
passes 173 tests in 13.69 seconds; Conductor validates 73 tracks without errors,
and whitespace validation passes. No full native rerun is claimed for this
documentation-only conflict resolution. The new pushed head requires fresh
hosted validation before merge.
