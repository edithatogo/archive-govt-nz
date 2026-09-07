# Source-contract integration validation

The first full `PYTEST_XDIST_AUTO_NUM_WORKERS=2 ./scripts/validate.sh`
attempt at `dc5ba26a21d3b4c2e14ae07d007456aa3d74228b` passed lock,
Conductor state (93 tracks), formatting, lint and typing. Pytest reported
5,932 passed and one collection error; coverage was 97.93%. The harness
exited 1 and later gates were not run.

`tests/test_build_foi_catalogue.py` imported `tools` as an installed package,
which is unavailable under the repository's direct pytest/importlib invocation.
The correction loads the local script through `runpy.run_path`, without
changing the application or global import path. The exact direct pytest
invocation reproduces the original error and passes the nine CLI tests after
correction. A complete corrected harness remains required before delivery.

Independent reviews cleared the bounded GDP/Crown context, guarded FOI
navigation and canonical index (454 focused tests), optional local canonical
CLI (106 focused tests), and metadata reserved-root correction (164 tests).
These focused reviews do not replace the complete integration gate.

## Corrected full gate

The corrected harness at `3a7b10235cba611304e9139235299cfc9ecf95ad`
completed with exit 0: all 5,941 tests passed, coverage remained above 95%,
all configured schema/mutation/hygiene gates passed, CAS throughput was
687.32 MB/s against a 25 MB/s minimum, and dependency audit, licence inventory,
secret scan and the validated 112-component SBOM passed. Independent re-review
used the exact direct-pytest importlib mode (106 focused tests, plus nine CLI
tests with two-worker loadscope) and cleared the collection correction.

This is local integration evidence, not hosted success or merged delivery.
The inherited PR #421 capture-resume provenance finding is being repaired
separately and must be integrated and validated before final merge. No source
rights, repair acceptance, publication or whole-track completion is granted.
