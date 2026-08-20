# Evidence

- Stacked base: `2c86d9001b07881f1c8af58146ec7a653bc740cf`.
- Merged CLI under correction: `src/archive_govt_nz/cli.py` legislation
  handlers introduced through PR #151.
- Corrected service dependency is present in the stacked base and remains
  represented upstream by unmerged PR #156.
- Implementation commit: `c92850b`.
- Critical authenticated-state module: 100% line and branch coverage across 18
  focused adversarial tests.
- CLI contract: 43 focused CLI tests passed; useful PR #151 command names,
  JSON fields, and bounded compatibility mappings are retained only where
  truthful.
- Affected suite: 119 tests passed across service, models, object store, CLI,
  and contract validation; all 15 contracts validated.
- Full harness partial result: 753 tests passed at 95.64% overall coverage plus
  lock, format, lint, typing, schemas, mutation, hygiene, and CAS benchmark.
- Supply chain: PyPI audit reported no known vulnerabilities; licence inventory,
  secret scan, and SBOM passed. The harness-required OSV service failed by
  external timeout/TLS transport on three invocations, so exact full-harness
  completion remains pending.
- Branch is local-only. No live or remote affirmative evidence was generated.
