# Evidence

- Stacked base: global CLI squash merge `138b17f`, incorporating service squash
  merge `394f210`.
- Merged CLI under correction: `src/archive_govt_nz/cli.py` legislation
  handlers introduced through PR #151.
- Corrected service and global CLI dependencies are merged through PRs #156 and
  #157 respectively.
- Implementation commit after rebase: `4d2e20c`.
- Critical authenticated-state module: 100% line and branch coverage across 18
  focused adversarial tests.
- CLI contract: 43 focused CLI tests passed; useful PR #151 command names,
  JSON fields, and bounded compatibility mappings are retained only where
  truthful.
- Affected suite: 119 tests passed across service, models, object store, CLI,
  and contract validation; all 15 contracts validated.
- Post-rebase integration audit found two inherited CLI tests still bypassed
  canonical discovery. They now supply canonical Work, Expression, and
  Manifestation graphs and pass through the corrected service path.
- Exact post-fix harness: 756 tests passed at 95.62% overall coverage; lock,
  format, lint, typing, schemas, all mutations, hygiene, CAS benchmark,
  dependency audit, licence inventory, secret scan, and SBOM passed.
- Post-merge-base harness: 756 tests passed at 95.62% overall coverage, with all
  repository gates green.
- No live or remote affirmative evidence was generated.
