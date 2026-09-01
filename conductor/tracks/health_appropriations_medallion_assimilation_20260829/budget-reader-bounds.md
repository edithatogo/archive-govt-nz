# Public Budget reader metadata bounds

This narrow follow-up retains the existing Budget v1 reader API, typed facts,
lineage, disposition joins, snapshots, row and expanded-byte limits. It inspects
at most five directory entries to enforce the exact four-file package closure,
and supplies 4 MiB Thrift string / 100,000 container limits when constructing
each ParquetFile, before metadata inspection or table materialization.
This is bounded transport consumption, not a hostile-Parquet sandbox, new
source semantics, original workbook capture, rights clearance or publication.
No raw packages, originals or HF objects are written.

## Red-first evidence

Five new tests include an exact four-entry success control and a generator that
fails if a sixth entry is requested, a constructor spy checking both caps before
decode, and two real-decoder tiny-cap rejection cases. Before implementation,
four failed and the control passed; receipt
`/tmp/health-budget-reader-bounds.ph7VOb-red.log` preserves the outcome.

First lint found a non-raw regex test literal, corrected without production
change. The first green run passed 61 tests but two new tests expected
ArrowException instead of the decoder's actual OSError size-limit failure;
correcting that expectation yielded all 63 passing. Strict typing then rejected
the spy's unrestricted keyword forwarding (four errors); explicit named cap
arguments resolved it without suppressions or production changes.

The focused critical gate passed all 63 tests in 4.63 seconds with 100% coverage
across 140 statements and 30 branches; Ruff and BasedPyright pass. Critical JSON
is retained at `/tmp/health-budget-reader-bounds.ph7VOb-critical.json`.
Independent parent and sibling review found no remaining issue at source SHA256
`ef514d9761961639547cee9e51ed998e4e6de70118fec40f402becfe8c4f8824`
and test SHA256
`45f62af3bdf439a62ccccd3858bb2f6a49ed5c025be443390bb9b6f1242d8f28`.

## Final local assurance

Functional checkpoint `4cdcaf57`; ordinary integration of delivered PR326
`cf2ec75b` produced `9dd1883a72c51df197ea7af98db8c9889073ec28` without
source/test changes or ledger conflicts. Cold unfiltered mutation then killed
all 112/112 mutants with 63 tests in 129.78 seconds, one worker, unchanged
30-second deadline, zero pardons and zero cache hits. The diagnostic coverage
warning during the no-coverage mutation run is not coverage evidence; the
separate strict critical gate above supplies coverage. Retained mutation JSON
SHA256 `97673af639afd34b9132f8d7989ae565c9eb5cbbdd9f5bb8324ab435b4ccb449`.

The native harness at exact `9dd1883a72c51df197ea7af98db8c9889073ec28`
exited 0: 4,239 tests, 8 existing warnings, 87.98 seconds, 97.38039294105884%
coverage; 76 Conductor tracks; 42 schemas / 32 samples; 9/9 parity; all native
mutation, hygiene, audit, licence, secret and 111-component SBOM gates passed.
CPython 3.14.6 / uv 0.11.8, ctrace, JIT disabled and four test workers were used.
Two unrelated harness-generated timestamp receipts were restored after exit.
Native log `/tmp/health-budget-reader-bounds.ph7VOb-native.log` SHA256
`2d072589d6d4986632dbf26812ada4a3b52970d0af969eee558138f919ac366e`;
native coverage JSON SHA256
`f53200498838e9f0f83eef3fb842118141e3b3e6ec2cce426ab25e16adcbb1dd`;
critical JSON SHA256
`f5fe90853185e74cebdddd3450d0234ba6afb7384683853450c76cbfbfc5d1e0`.

Commands: focused `.venv/bin/pytest tests/domains/health_appropriations/test_budget_reader.py
-q --no-cov`; critical adds the exact reader module `--cov`, `--cov-branch` and
`--cov-fail-under=100`; cold uses the same full test file with `--gremlins`, the
reader `--gremlin-targets`, `--gremlin-parallel --gremlin-workers=1`,
`--gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons
--gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov`.
Full gate: `COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4
./scripts/validate.sh` with an isolated UV cache. Exact-head hosted delivery
remains separate; no source capture, output dataset or publication occurred.
## Hosted Windows timeout remediation

The first Windows hosted run and one unchanged retry both exhausted the existing
300-second command limit during the full pytest phase without an assertion or
traceback. Attempt one reached 78%; attempt two reached 57%, demonstrating
runner-throughput variability rather than a stable failing test. The retained
attempt-two log SHA-256 is
`424528c35dd8141f8ab6e1c7b3860633ec2c2f6fbab5bdc969be0c21547c882a`.

The CI invocation now uses the repository's existing `auto` pytest-worker mode,
matching both native validation scripts, while preserving the same locked
harness, load-scope distribution, full test set, coverage threshold, 300-second
command limit and every post-test gate. This is a throughput correction, not a
timeout, threshold or validation reduction. Fresh exact-head hosted results are
required before delivery.
