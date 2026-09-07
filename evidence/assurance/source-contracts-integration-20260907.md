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
