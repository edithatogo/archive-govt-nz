# Stage 2: opt-in eight-stage orchestration and verified coverage

Depends on packaging commit `6c4805e9d76b103cc56d351cf0fb1e6e605e2150`.
Same isolated base `de2d3a25e3f09ed520a238b22a61cde11f70e5fe`.
M-04/M-07/M-15/M-16/M-18; AC-03/AC-05/AC-12/AC-13/AC-16.

## Operational contract

The existing `health-appropriations-rebuild` command accepts `--eight-stage`
only with explicit `--crown-source-sha256`. Dry-run remains the default;
`--no-dry-run` creates the separately versioned `health-raw-rebuild/v2` run.
`health-appropriations-verify-rebuild --eight-stage` reads an independently
pinned completed run without reconstructing it. Do not pass v2 runs to v1
resume, raw compatibility or Gold consumers.

Exactly eight stages are declared: budget, befu, hyefu, historical, revenue,
befu-detail, hyefu-detail, crown. The first four call the unchanged v1
dispatcher and receipt verifier; `rebuild.PROFILES` is unchanged. Revenue uses
its existing writer and the final three use the stage-1 packaging boundary.
No new extraction semantics, independent reader, chart adapter, mapping,
Gold calculation or source capture is introduced.

The v2 plan embeds exact pinned donor-manifest bytes and the original four-stage
plan. Every donor selection must join one unique path/object/hash; detail and
summary stages intentionally share source objects without being combined.
Crown's explicit direct-object pin is verified separately in CAS against the
approved Fiscal 2025 admission hash, source URL and vintage. It is not inserted
into the 23-file donor census. This explicit object binding does not claim new
capture receipt verification or a rights grant. Crown retains its source
observation time/ID; caller-supplied donor observation context is distinct from
the time the new command runs.

Plans preflight before output creation. Output directories and stage files use
existing exclusive writers. Failed runs retain PLAN, partial stages and a
redacted FAILURE receipt without a completion manifest; retry needs a new
directory. Completed-run reuse requires identical plan and fresh source,
package and coverage verification. V1 resume is not extended or repurposed.

## Coverage assurance and limits

The completed manifest contains one source/stage-pinned coverage entry per
stage: record IDs, fact/lineage/disposition counts, reason-code counts, exact
disposition-file hash and existing other-sheet exclusions. Verification reads
existing persisted schemas with the shared bounded Parquet reader, checks
source/observation context, amount lineage, unique records, and disposition
joins. New literal selections must match their approved coordinate sets;
formula exclusions and whole-sheet-minus-selection remainders must agree.
Revenue requires all 1000 row occurrences and 69 facts. Global record-ID
uniqueness prevents cross-stage aliasing.

Coverage remains adapter-scoped. A sheet preserved by one adapter can have
selected cells admitted by another; those contexts are not contradictory global
states. Named remainder expressions are not a claim that every source area has
been semantically normalized. Existing area-accounting v1 remains its honest
metadata/assertion-only API, unchanged; v2 operational coverage is constructed
from verified output packages rather than upgrading those assertions.

This is internal retained-artifact consistency and lineage accounting, not
authenticity against coordinated rewriting of every artifact/pin. In particular,
the verifier does not rerun a second semantic extraction from source bytes.
Original source-specific replay evidence remains authoritative for extraction
semantics. Rights stay `not_evaluated`; Gold selection/publication stay
`not_performed`. The 290 additional observations are not a financial sum.

## TDD and focused validation

Initial orchestration test failed on missing module. Fault tests cover donor
hash/source joins, distinct direct Crown pin, dropped/duplicate facts and
dispositions, orphan lineage, altered amounts/source/context/schema, conflicting
remainders/formula states, changed artifact hashes, interrupted/existing runs,
CLI opt-in requirements, and no-change v1 behavior. A self-review regression
proved cross-stage duplicate IDs were previously accepted; the final completion
join now rejects them. Missing-run CLI handling was characterized green.

Commands run with the existing repository environment and `PYTHONPATH=src`:

```sh
python -m pytest tests/domains/health_appropriations/test_rebuild_eight.py tests/domains/health_appropriations/test_verified_coverage.py -q --cov=archive_govt_nz.domains.health_appropriations.rebuild_eight --cov=archive_govt_nz.domains.health_appropriations.verified_coverage --cov-branch --cov-report=term-missing
# 78 passed; 194/194 statements and 42/42 branches covered.
python -m pytest tests/domains/health_appropriations/test_rebuild_eight.py tests/domains/health_appropriations/test_verified_coverage.py tests/domains/health_appropriations/test_rebuild.py tests/domains/health_appropriations/test_rebuild_resume.py tests/domains/health_appropriations/test_rebuild_completion.py -q
# 234 passed.
python -m pytest tests/domains/health_appropriations/test_rebuild_eight.py tests/domains/health_appropriations/test_verified_coverage.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/rebuild_eight.py,src/archive_govt_nz/domains/health_appropriations/verified_coverage.py --gremlin-clear-cache --gremlin-no-coverage-filter --gremlin-workers=4
# 155/155 killed, zero survivors and zero cache hits.
```

The preceding coverage-selected mutation run reported 154 kills and one survivor
at the failure-receipt path operation. Its JSON selected only the profile-list
test for that mutation. The cold unfiltered run above exercised the actual
failure tests and killed it, with no production change or pardon. Both mutation
runs emitted the previously-imported-module warning; separate focused coverage
is the source of the coverage figures above. Ruff check/format and basedpyright
passed on new modules/tests, CLI and replay recipe.

Final replay is recorded in `orchestration-replay.json`: both directories under
`/tmp/health-eight-stage.znzmQf` have identical file hashes and completed-manifest
SHA-256 `a2dc3fb25cbe2e3cbd5d137f458cb6b5f02d5dad4d245011f460451048119d7b`.

`replay_eight.py ARCHIVE_ROOT NEW_OUTPUT_ROOT` builds two new retained-source
runs and checks pinned read-only verification and every output file hash. It
requires 69 revenue, 80 BEFU detail, 80 HYEFU detail and 61 Crown observations;
the original four produce 215/10/10/106 respectively. No source payloads enter
Git. Stage-1 replay separately compared every new literal record document and
amount against existing admissions; the prior revenue replay independently
checked every original XML row and context link.

Conductor implement/review guided the scoped implementation and self-review.
No full harness, shared lifecycle edits, parent-tree changes, push, merge or
publication. Independent review and full integrated validation remain parent
responsibilities. Future coordinate-free Faraday chart extractions are outside
this exact eight-stage contract.
