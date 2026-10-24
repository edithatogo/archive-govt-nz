# PDF dependency security unblock — 2026-10-22

The first Phase 4 final-tree harness passed 8,283 tests, schemas, parity and
mutation checks, then failed its original OSV audit on four vulnerabilities
in `pypdf 6.19.0`. The terminal failed run, audit receipt and unchanged-pin
postflight are retained; this is not an all-stage pass.

The supported 6.x dependency is now locked to 6.21.1, with a matching minimum
version in the project contract. The [maintainer changelog](https://pypdf.readthedocs.io/en/6.21.1/meta/CHANGELOG.html)
records the security fixes. Only pypdf and the root project's dependency
specifier change in the lock; no other package is upgraded.

The original audit now reports no known vulnerabilities. All 60 existing
focused PDF tests pass. Exact retained 1999/2000 overview, 2016/17 category
and 2025/26 summary profiles rebuild 22 facts and all 12 package files match
their retained bytes. Original source hashes remain unchanged. Existing
non-zero-indexed-xref reader warnings are preserved in the bounded log; no
source bytes are repaired or rewritten. These are three qualified source
areas, not a claim of whole-PDF or all-vintage requalification.

The prior 188 Phase 4 native output/summary files remain unchanged. That native
producer keeps its original dependency context; the later update deliberately
changes only `pyproject.toml` and `uv.lock` outside Conductor. All other frozen
native code/control/source/render-runtime pins still match. The paired JSON
binds both observations without rewriting earlier receipts.

Fresh final-tree original validation and hosted checks, including dependency
review, remain required before protected merge. Coverage stays at 80%; no tests,
limits, protections, financial values, rights or publication decisions change.
Refs #205, #210, #215.
